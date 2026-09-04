"""Services de placement rectangulaire et génération transactionnelle des chutes."""
from dataclasses import dataclass, field
from django.db import transaction
from chutes.models import Chute
from emplacements.models import Emplacement
from panneaux.models import Panneau
from .models import Decoupe
from mouvements.models import Mouvement
from chutes.services import utiliser

MINIMUM_MM = 100
# Nombre d'agencements conservés à chaque étape. Cette limite évite que le calcul
# ne ralentisse l'interface lorsque beaucoup de pièces sont demandées.
MAX_PLAN_STATES = 160
@dataclass(frozen=True)
class Rectangle:
    longueur: int
    largeur: int
    x: int = field(default=0, compare=False)
    y: int = field(default=0, compare=False)


def emplacement_automatique() -> Emplacement:
    """Assign generated offcuts to the least-used cart from 1 to 99."""
    emplacements = []
    for numero in range(1, 100):
        emplacement, _ = Emplacement.objects.get_or_create(
            chariot=str(numero), niveau=1, case=1,
            defaults={"code": f"AUTO-{numero:02d}-1-1", "description": "Stockage automatique"},
        )
        if emplacement.actif:
            emplacements.append(emplacement)
    return min(emplacements, key=lambda item: (Chute.objects.filter(emplacement=item, etat=Chute.Etat.DISPONIBLE).count(), int(item.chariot)))

def _split_leftovers(source: Rectangle, cut: Rectangle, horizontal_first: bool) -> tuple[list[Rectangle], int]:
    """Retourne les chutes exploitables et la surface écartée par une coupe guillotine."""
    if cut.longueur > source.longueur or cut.largeur > source.largeur:
        raise ValueError("Découpe hors panneau")
    if horizontal_first:
        raw = [
            Rectangle(source.longueur, source.largeur - cut.largeur, source.x, source.y + cut.largeur),
            Rectangle(source.longueur - cut.longueur, cut.largeur, source.x + cut.longueur, source.y),
        ]
    else:
        raw = [
            Rectangle(source.longueur - cut.longueur, source.largeur, source.x + cut.longueur, source.y),
            Rectangle(cut.longueur, source.largeur - cut.largeur, source.x, source.y + cut.largeur),
        ]
    restes = [rectangle for rectangle in raw if rectangle.longueur >= MINIMUM_MM and rectangle.largeur >= MINIMUM_MM]
    perte = sum(rectangle.longueur * rectangle.largeur for rectangle in raw if rectangle not in restes)
    return restes, perte


def _plan_score(perte: int, libres: list[Rectangle]) -> tuple[int, int, int, int]:
    """Préserve la matière récupérable et privilégie la plus grande chute possible."""
    surfaces = [rectangle.longueur * rectangle.largeur for rectangle in libres]
    return perte, -max(surfaces, default=0), -sum(surface * surface for surface in surfaces), len(libres)


def planifier_panneau(longueur: int, largeur: int, demandes: list[tuple[int, int]]) -> tuple[list[dict], list[Rectangle]]:
    """Optimise un plan de coupe guillotine, avec rotations admises.

    Plusieurs ordres de pièces, emplacements et sens de séparation sont évalués.
    Le plan retenu minimise la matière non récupérable, puis maximise la surface de
    la plus grande chute utilisable. Le nombre de chutes est seulement un critère
    de départage final.
    """
    if not demandes:
        return [], [Rectangle(longueur, largeur)]

    # État : (surface perdue, demandes restantes, zones libres, pièces posées).
    etats = [(0, tuple(enumerate(demandes)), [Rectangle(longueur, largeur)], [])]
    for _ in demandes:
        suivants = []
        for perte, restantes, libres, poses in etats:
            for demande_index, (demande_longueur, demande_largeur) in restantes:
                autres = tuple(item for item in restantes if item[0] != demande_index)
                for libre_index, libre in enumerate(libres):
                    orientations = [(demande_longueur, demande_largeur, False)]
                    if demande_longueur != demande_largeur:
                        orientations.append((demande_largeur, demande_longueur, True))
                    for cut_longueur, cut_largeur, rotation in orientations:
                        if cut_longueur > libre.longueur or cut_largeur > libre.largeur:
                            continue
                        cut = Rectangle(cut_longueur, cut_largeur)
                        for horizontal_first in (False, True):
                            restes, perte_supplementaire = _split_leftovers(libre, cut, horizontal_first)
                            nouveaux_libres = libres[:libre_index] + libres[libre_index + 1:] + restes
                            pose = {
                                "longueur": demande_longueur, "largeur": demande_largeur, "rotation": rotation,
                                "x": libre.x, "y": libre.y, "plan_longueur": cut.longueur, "plan_largeur": cut.largeur,
                            }
                            suivants.append((perte + perte_supplementaire, autres, nouveaux_libres, poses + [pose]))
        if not suivants:
            raise ValueError("Au moins une découpe ne rentre pas dans la matière restante.")
        suivants.sort(key=lambda etat: _plan_score(etat[0], etat[2]))
        etats = suivants[:MAX_PLAN_STATES]

    perte, _, restes, poses = min(etats, key=lambda etat: _plan_score(etat[0], etat[2]))
    return poses, restes

@transaction.atomic
def appliquer_plan_panneau(panneau, demandes: list[tuple[int, int]], emplacement, user=None, piece_production=None):
    panneau = Panneau.objects.select_for_update().get(pk=panneau.pk)
    if panneau.statut != Panneau.Statut.DISPONIBLE:
        raise ValueError("Ce panneau n'est plus disponible pour une d\u00e9coupe.")
    """Valide un plan prévisualisé et crée les découpes/chutes résultantes."""
    poses, restes = planifier_panneau(panneau.longueur, panneau.largeur, demandes)
    common = {"type_verre": panneau.type_verre, "epaisseur": panneau.epaisseur, "teinte": panneau.teinte}
    panneau.statut = "EPUISE"; panneau.save(update_fields=["statut"])
    for pose in poses:
        Decoupe.objects.create(panneau=panneau, longueur=pose["longueur"], largeur=pose["largeur"], utilisateur=user, piece_production=piece_production)
    creees = [Chute.objects.create(**common, emplacement=emplacement, longueur=r.longueur, largeur=r.largeur, origine=f"Panneau {panneau.reference}") for r in restes]
    Mouvement.objects.create(utilisateur=user, action="DECOUPE_PANNEAU", objet=panneau.reference, commentaire=f"{len(poses)} découpe(s), {len(creees)} chute(s) créée(s)")
    return poses, creees

def compatibles(longueur: int, largeur: int, **specs):
    """Retourne les chutes compatibles, triées par perte croissante (rotation admise)."""
    qs=Chute.objects.select_related("emplacement", "type_verre", "epaisseur", "teinte").filter(etat=Chute.Etat.DISPONIBLE, **specs)
    candidates=[c for c in qs if (c.longueur >= longueur and c.largeur >= largeur) or (c.longueur >= largeur and c.largeur >= longueur)]
    def score(chute):
        # La perte de surface est prioritaire. A égalité, la chute dont les
        # deux dimensions sont les plus proches de la pièce passe en tête.
        orientations = []
        if chute.longueur >= longueur and chute.largeur >= largeur:
            orientations.append((chute.longueur - longueur, chute.largeur - largeur))
        if chute.longueur >= largeur and chute.largeur >= longueur:
            orientations.append((chute.longueur - largeur, chute.largeur - longueur))
        surplus_longueur, surplus_largeur = min(
            orientations,
            key=lambda surplus: (sum(surplus), max(surplus)),
        )
        return (
            chute.longueur * chute.largeur - longueur * largeur,
            surplus_longueur + surplus_largeur,
            max(surplus_longueur, surplus_largeur),
            chute.date_creation,
        )

    return sorted(candidates, key=score)

def leftovers(source: Rectangle, cut: Rectangle) -> list[Rectangle]:
    """Découpe en guillotine: la bande droite et la bande basse sont les restes."""
    return _split_leftovers(source, cut, horizontal_first=False)[0]


def previsualiser_utilisation_chute(chute, longueur: int, largeur: int) -> dict:
    """Prévoit l'orientation et les chutes réutilisables après une découpe.

    Cette simulation utilise exactement les mêmes règles que ``consume`` : une
    rotation est admise et seuls les rectangles d'au moins 100 mm sont gardés.
    """
    normale = longueur <= chute.longueur and largeur <= chute.largeur
    tournee = longueur <= chute.largeur and largeur <= chute.longueur
    if not (normale or tournee):
        raise ValueError("La decoupe demandee ne rentre pas dans la chute.")
    rotation = tournee and not normale
    coupe = Rectangle(largeur, longueur) if rotation else Rectangle(longueur, largeur)
    return {"rotation": rotation, "restes": leftovers(Rectangle(chute.longueur, chute.largeur), coupe)}

@transaction.atomic
def consume(source, longueur: int, largeur: int, user=None, emplacement=None, stocker_restes=True, piece_production=None):
    if isinstance(source, Chute):
        source = Chute.objects.select_for_update().get(pk=source.pk)
        if source.etat != Chute.Etat.DISPONIBLE:
            raise ValueError("Cette chute n'est plus disponible pour une d\u00e9coupe.")
    else:
        source = source.__class__.objects.select_for_update().get(pk=source.pk)
        if source.statut != "DISPONIBLE":
            raise ValueError("Ce panneau n'est plus disponible pour une d\u00e9coupe.")
    """Consomme une chute/panneau et, sauf choix contraire, stocke les restes valides."""
    if not ((longueur <= source.longueur and largeur <= source.largeur) or (longueur <= source.largeur and largeur <= source.longueur)):
        raise ValueError("La decoupe demandee ne rentre pas dans la matiere selectionnee.")
    rotated = longueur <= source.largeur and largeur <= source.longueur and not (longueur <= source.longueur and largeur <= source.largeur)
    cut=Rectangle(largeur, longueur) if rotated else Rectangle(longueur, largeur)
    restes=leftovers(Rectangle(source.longueur,source.largeur),cut)
    common={"type_verre":source.type_verre,"epaisseur":source.epaisseur,"teinte":source.teinte}
    emplacement=emplacement or getattr(source,"emplacement",None) or Chute.objects.filter(**common,etat=Chute.Etat.DISPONIBLE).values_list("emplacement",flat=True).first()
    if not emplacement: raise ValueError("Choisissez un emplacement pour créer les chutes.")
    if isinstance(source, Chute):
        utiliser(source.pk, user, f"Découpe {longueur}×{largeur}")
        source.refresh_from_db()
    else: source.statut="EPUISE"; source.save(update_fields=["statut"])
    d=Decoupe.objects.create(**({"chute_source":source} if isinstance(source,Chute) else {"panneau":source}), longueur=longueur,largeur=largeur,utilisateur=user,piece_production=piece_production)
    emplacement_id=getattr(emplacement,"pk",emplacement)
    if stocker_restes:
        for r in restes: Chute.objects.create(**common, emplacement_id=emplacement_id, longueur=r.longueur, largeur=r.largeur, origine=f"Découpe {d.pk}")
    else:
        restes = []
    Mouvement.objects.create(utilisateur=user,action="UTILISATION_CHUTE" if isinstance(source,Chute) else "DECOUPE_PANNEAU",objet=str(source),commentaire=f"Découpe {longueur}×{largeur}")
    return d, restes

@transaction.atomic
def consume_batch(source, lignes: list[tuple[int, int]], user=None, emplacement=None):
    """Réalise plusieurs découpes en recherchant une chute avant chaque panneau."""
    if not lignes:
        raise ValueError("Aucune découpe demandée.")
    resultats = []
    courant = source
    for index, (longueur, largeur) in enumerate(lignes):
        if index:
            specs = {"type_verre": source.type_verre, "epaisseur": source.epaisseur, "teinte": source.teinte}
            choix = compatibles(longueur, largeur, **specs)
            if not choix:
                raise ValueError(f"Aucune chute compatible pour {longueur} × {largeur} mm.")
            courant = choix[0]
        resultats.append(consume(courant, longueur, largeur, user, emplacement))
    return resultats
