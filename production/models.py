from django.conf import settings
from django.db import models
from commandes.models import Commande, LigneCommande


class FicheProduction(models.Model):
    class Statut(models.TextChoices): A_PREPARER="A_PREPARER", "À préparer"; EN_COURS="EN_COURS", "En cours"; BLOQUEE="BLOQUEE", "Bloquée"; TERMINEE="TERMINEE", "Terminée"
    reference=models.CharField(max_length=24,unique=True,blank=True); commande=models.ForeignKey(Commande,on_delete=models.PROTECT,related_name="fiches_production"); statut=models.CharField(max_length=16,choices=Statut.choices,default=Statut.A_PREPARER); priorite=models.CharField(max_length=10,default="NORMALE"); cree_le=models.DateTimeField(auto_now_add=True); cree_par=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.SET_NULL)
    class Meta: permissions=[("manage_production", "Peut gérer la production"), ("operate_production", "Peut opérer les étapes de production"), ("control_quality", "Peut effectuer le contrôle qualité")]
    def save(self,*args,**kwargs):
        if not self.reference: self.reference=f"FP-{self.cree_le.year if self.cree_le else 2026}-{FicheProduction.objects.count()+1:04d}"
        super().save(*args,**kwargs)
    def __str__(self): return self.reference

class PieceProduction(models.Model):
    fiche=models.ForeignKey(FicheProduction,on_delete=models.CASCADE,related_name="pieces"); ligne_commande=models.ForeignKey(LigneCommande,on_delete=models.PROTECT); reference=models.CharField(max_length=50); quantite=models.PositiveIntegerField(); statut=models.CharField(max_length=16,default="A_FAIRE")

class EtapeProduction(models.Model):
    class Type(models.TextChoices): DECOUPE="DECOUPE", "Découpe"; RABOTAGE="RABOTAGE", "Rabotage"; PERCAGE="PERCAGE", "Perçage"; TREMPE="TREMPE", "Trempe"; CONTROLE="CONTROLE", "Contrôle qualité"
    class Statut(models.TextChoices): A_FAIRE="A_FAIRE", "À faire"; EN_COURS="EN_COURS", "En cours"; TERMINE="TERMINE", "Terminée"; BLOQUE="BLOQUE", "Bloquée"; NON_CONFORME="NON_CONFORME", "Non conforme"
    piece=models.ForeignKey(PieceProduction,on_delete=models.CASCADE,related_name="etapes"); type=models.CharField(max_length=12,choices=Type.choices); statut=models.CharField(max_length=16,choices=Statut.choices,default=Statut.A_FAIRE); operateur=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.SET_NULL); debut=models.DateTimeField(null=True,blank=True); fin=models.DateTimeField(null=True,blank=True); commentaire=models.TextField(blank=True); probleme=models.TextField(blank=True)
    class Meta: unique_together=[("piece","type")]
