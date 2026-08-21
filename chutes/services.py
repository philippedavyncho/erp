"""Transitions métier traçables des chutes de verre."""

from django.db import transaction

from mouvements.models import Mouvement
from .models import Chute, MouvementChute


def _dimensions(chute):
    return f"{chute.longueur} × {chute.largeur} mm"


def _history(chute, action, user, **fields):
    MouvementChute.objects.create(chute=chute, action=action, utilisateur=user, **fields)
    Mouvement.objects.create(utilisateur=user, action=f"CHUTE_{action}", objet=chute.numero, commentaire=fields.get("commentaire", ""))


def _locked(chute_id):
    return Chute.objects.select_for_update().get(pk=chute_id)


@transaction.atomic
def deplacer(chute_id, nouvel_emplacement, user, commentaire=""):
    chute = _locked(chute_id)
    if chute.etat in (Chute.Etat.UTILISEE, Chute.Etat.REBUT):
        raise ValueError("Une chute utilisée ou au rebut ne peut pas être déplacée.")
    ancien = chute.emplacement
    if ancien == nouvel_emplacement:
        raise ValueError("Le nouvel emplacement doit être différent de l'emplacement actuel.")
    chute.emplacement, chute.modifie_par = nouvel_emplacement, user
    chute.save()
    _history(chute, MouvementChute.Action.DEPLACEMENT, user, ancien_emplacement=ancien, nouvel_emplacement=nouvel_emplacement, commentaire=commentaire)
    return chute


@transaction.atomic
def corriger(chute_id, data, user, commentaire=""):
    chute = _locked(chute_id)
    if chute.etat in (Chute.Etat.UTILISEE, Chute.Etat.REBUT):
        raise ValueError("Une chute utilisée ou au rebut ne peut pas être corrigée.")
    anciennes_dimensions = _dimensions(chute)
    ancienne_description = f"{chute.type_verre} · {chute.epaisseur} · {chute.teinte}"
    for field in ("longueur", "largeur", "type_verre", "epaisseur", "teinte", "emplacement"):
        setattr(chute, field, data[field])
    chute.modifie_par = user
    chute.save()
    nouvelle_description = f"{chute.type_verre} · {chute.epaisseur} · {chute.teinte}"
    _history(chute, MouvementChute.Action.CORRECTION, user, ancien_emplacement=None, nouvel_emplacement=None,
             anciennes_dimensions=f"{anciennes_dimensions} — {ancienne_description}",
             nouvelles_dimensions=f"{_dimensions(chute)} — {nouvelle_description}", commentaire=commentaire)
    return chute


@transaction.atomic
def reserver(chute_id, reference, user, commentaire=""):
    chute = _locked(chute_id)
    if chute.etat != Chute.Etat.DISPONIBLE:
        raise ValueError("Seule une chute disponible peut être réservée.")
    chute.etat, chute.reservation_reference, chute.modifie_par = Chute.Etat.RESERVEE, reference, user
    chute.save()
    _history(chute, MouvementChute.Action.RESERVATION, user, ancien_statut=Chute.Etat.DISPONIBLE,
             nouveau_statut=Chute.Etat.RESERVEE, commentaire=commentaire or f"Référence : {reference}")
    return chute


@transaction.atomic
def annuler_reservation(chute_id, user, commentaire=""):
    chute = _locked(chute_id)
    if chute.etat != Chute.Etat.RESERVEE:
        raise ValueError("Cette chute n'est pas réservée.")
    chute.etat, chute.reservation_reference, chute.modifie_par = Chute.Etat.DISPONIBLE, "", user
    chute.save()
    _history(chute, MouvementChute.Action.ANNULATION_RESERVATION, user, ancien_statut=Chute.Etat.RESERVEE,
             nouveau_statut=Chute.Etat.DISPONIBLE, commentaire=commentaire)
    return chute


@transaction.atomic
def utiliser(chute_id, user, commentaire=""):
    chute = _locked(chute_id)
    if chute.etat not in (Chute.Etat.DISPONIBLE, Chute.Etat.RESERVEE):
        raise ValueError("Cette chute ne peut pas être utilisée dans son état actuel.")
    ancien = chute.etat
    chute.etat, chute.reservation_reference, chute.modifie_par = Chute.Etat.UTILISEE, "", user
    chute.save()
    _history(chute, MouvementChute.Action.UTILISATION, user, ancien_statut=ancien,
             nouveau_statut=Chute.Etat.UTILISEE, commentaire=commentaire)
    return chute


@transaction.atomic
def mettre_au_rebut(chute_id, motif, user, commentaire=""):
    chute = _locked(chute_id)
    if motif not in dict(MouvementChute.MotifRebut.choices):
        raise ValueError("Un motif de rebut est obligatoire.")
    if chute.etat in (Chute.Etat.UTILISEE, Chute.Etat.REBUT):
        raise ValueError("Cette chute ne peut pas être mise au rebut dans son état actuel.")
    ancien = chute.etat
    chute.etat, chute.reservation_reference, chute.modifie_par = Chute.Etat.REBUT, "", user
    chute.save()
    _history(chute, MouvementChute.Action.REBUT, user, ancien_statut=ancien,
             nouveau_statut=Chute.Etat.REBUT, motif=motif, commentaire=commentaire)
    return chute
