from django.db import transaction
from django.utils import timezone
from commandes.models import Commande
from .models import EtapeProduction, FicheProduction, PieceProduction
@transaction.atomic
def creer_fiche(commande,user):
    if commande.statut not in (Commande.Statut.VALIDEE,Commande.Statut.EN_PREPARATION): raise ValueError("La commande doit être validée.")
    if commande.fiches_production.exists():
        raise ValueError("Une fiche de production existe déjà pour cette commande.")
    fiche=FicheProduction.objects.create(commande=commande,priorite=commande.priorite,cree_par=user)
    for index,line in enumerate(commande.lignes.all(),1):
        piece=PieceProduction.objects.create(fiche=fiche,ligne_commande=line,reference=f"{fiche.reference}-{index}",quantite=line.quantite)
        for operation,required in [(EtapeProduction.Type.DECOUPE,line.decoupe),(EtapeProduction.Type.RABOTAGE,line.rabotage),(EtapeProduction.Type.PERCAGE,line.percage),(EtapeProduction.Type.TREMPE,line.trempe),(EtapeProduction.Type.CONTROLE,True)]:
            if required: EtapeProduction.objects.create(piece=piece,type=operation)
    commande.statut=Commande.Statut.EN_PREPARATION; commande.save(update_fields=["statut"]); return fiche
@transaction.atomic
def changer_etape(etape,statut,user,commentaire="",probleme=""):
    etape=EtapeProduction.objects.select_for_update().get(pk=etape.pk); etape.statut=statut; etape.operateur=user; etape.commentaire=commentaire; etape.probleme=probleme
    if statut==EtapeProduction.Statut.EN_COURS: etape.debut=timezone.now()
    if statut in (EtapeProduction.Statut.TERMINE,EtapeProduction.Statut.NON_CONFORME): etape.fin=timezone.now()
    etape.save(); return etape
