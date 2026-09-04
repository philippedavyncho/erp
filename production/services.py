from django.db import transaction
from django.utils import timezone
from commandes.models import Commande, HistoriqueCommande
from .models import EtapeProduction, FicheProduction, PieceProduction
@transaction.atomic
def creer_fiche(commande,user):
    commande = Commande.objects.select_for_update().get(pk=commande.pk)
    if commande.statut not in (Commande.Statut.VALIDEE,Commande.Statut.EN_PREPARATION): raise ValueError("La commande doit être validée.")
    if commande.fiches_production.exists():
        raise ValueError("Une fiche de production existe déjà pour cette commande.")
    fiche=FicheProduction.objects.create(commande=commande,priorite=commande.priorite,cree_par=user)
    for index,line in enumerate(commande.lignes.all(),1):
        piece=PieceProduction.objects.create(fiche=fiche,ligne_commande=line,reference=f"{fiche.reference}-{index}",quantite=line.quantite)
        for operation,required in [(EtapeProduction.Type.DECOUPE,line.decoupe),(EtapeProduction.Type.RABOTAGE,line.rabotage),(EtapeProduction.Type.PERCAGE,line.percage),(EtapeProduction.Type.TREMPE,line.trempe),(EtapeProduction.Type.CONTROLE,True)]:
            if required: EtapeProduction.objects.create(piece=piece,type=operation)
    if commande.statut == Commande.Statut.VALIDEE:
        ancien_statut = commande.statut
        commande.statut = Commande.Statut.EN_PREPARATION
        commande.save(update_fields=["statut"])
        HistoriqueCommande.objects.create(
            commande=commande,
            ancien_statut=ancien_statut,
            nouveau_statut=commande.statut,
            utilisateur=user,
            commentaire=f"Fiche de production {fiche.reference} cr\u00e9\u00e9e.",
        )
    return fiche
@transaction.atomic
def changer_etape(etape,statut,user,commentaire="",probleme=""):
    etape=EtapeProduction.objects.select_for_update().select_related("piece__fiche__commande").get(pk=etape.pk)
    if statut not in EtapeProduction.Statut.values:
        raise ValueError("Statut d'op\u00e9ration invalide.")
    ordre = [EtapeProduction.Type.DECOUPE, EtapeProduction.Type.RABOTAGE, EtapeProduction.Type.PERCAGE, EtapeProduction.Type.TREMPE, EtapeProduction.Type.CONTROLE]
    if statut == EtapeProduction.Statut.EN_COURS:
        position = ordre.index(etape.type)
        precedentes = etape.piece.etapes.filter(type__in=ordre[:position]).exclude(statut=EtapeProduction.Statut.TERMINE)
        if precedentes.exists():
            raise ValueError("L'opération précédente doit être terminée avant de démarrer celle-ci.")
    if statut == EtapeProduction.Statut.TERMINE and etape.statut != EtapeProduction.Statut.EN_COURS:
        raise ValueError("Une opération doit être démarrée avant d'être terminée.")
    etape.statut=statut; etape.operateur=user; etape.commentaire=commentaire; etape.probleme=probleme
    if statut==EtapeProduction.Statut.EN_COURS: etape.debut=timezone.now()
    if statut in (EtapeProduction.Statut.TERMINE,EtapeProduction.Statut.NON_CONFORME): etape.fin=timezone.now()
    etape.save()
    _synchroniser_avancement(etape.piece.fiche, user)
    return etape


def _synchroniser_avancement(fiche, user):
    """Répercute l'avancement de l'atelier sur la fiche et la commande."""
    fiche = FicheProduction.objects.select_for_update().select_related("commande").get(pk=fiche.pk)
    etapes = EtapeProduction.objects.filter(piece__fiche=fiche)
    statuts = list(etapes.values_list("statut", flat=True))
    nouveau_statut = fiche.statut
    if any(statut in (EtapeProduction.Statut.BLOQUE, EtapeProduction.Statut.NON_CONFORME) for statut in statuts):
        nouveau_statut = FicheProduction.Statut.BLOQUEE
    elif statuts and all(statut == EtapeProduction.Statut.TERMINE for statut in statuts):
        nouveau_statut = FicheProduction.Statut.TERMINEE
    elif any(statut in (EtapeProduction.Statut.EN_COURS, EtapeProduction.Statut.TERMINE) for statut in statuts):
        nouveau_statut = FicheProduction.Statut.EN_COURS
    if nouveau_statut != fiche.statut:
        fiche.statut = nouveau_statut
        fiche.save(update_fields=["statut"])

    commande = fiche.commande
    cible_commande = None
    if nouveau_statut == FicheProduction.Statut.EN_COURS and commande.statut == Commande.Statut.EN_PREPARATION:
        cible_commande = Commande.Statut.EN_PRODUCTION
    elif nouveau_statut == FicheProduction.Statut.TERMINEE and commande.statut == Commande.Statut.EN_PRODUCTION:
        cible_commande = Commande.Statut.TERMINEE
    if cible_commande:
        ancien_statut = commande.statut
        commande.statut = cible_commande
        commande.save(update_fields=["statut"])
        HistoriqueCommande.objects.create(commande=commande, ancien_statut=ancien_statut, nouveau_statut=cible_commande, utilisateur=user, commentaire=f"Mise à jour automatique depuis la fiche {fiche.reference}")
