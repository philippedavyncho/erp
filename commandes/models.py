from django.conf import settings
from django.db import models
from clients.models import Client
from commercial.models import Devis
from types_verres.models import Epaisseur, TypeVerre


class Commande(models.Model):
    class Statut(models.TextChoices):
        NOUVELLE="NOUVELLE", "Nouvelle"; VALIDEE="VALIDEE", "Validée"; EN_PREPARATION="EN_PREPARATION", "En préparation"; EN_PRODUCTION="EN_PRODUCTION", "En production"; TERMINEE="TERMINEE", "Terminée"; PRETE="PRETE", "Prête"; LIVREE="LIVREE", "Livrée"; ANNULEE="ANNULEE", "Annulée"
    class Priorite(models.TextChoices): NORMALE="NORMALE", "Normale"; HAUTE="HAUTE", "Haute"; URGENTE="URGENTE", "Urgente"
    reference=models.CharField(max_length=24,unique=True,blank=True); client=models.ForeignKey(Client,on_delete=models.PROTECT,related_name="commandes"); devis=models.OneToOneField(Devis,null=True,blank=True,on_delete=models.PROTECT,related_name="commande")
    statut=models.CharField(max_length=20,choices=Statut.choices,default=Statut.NOUVELLE); date=models.DateField(auto_now_add=True); date_prevue=models.DateField(null=True,blank=True); priorite=models.CharField(max_length=10,choices=Priorite.choices,default=Priorite.NORMALE); commentaire=models.TextField(blank=True)
    cree_par=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.SET_NULL,related_name="commandes_creees"); valide_par=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.SET_NULL,related_name="commandes_validees")
    class Meta:
        ordering=["-date","-pk"]
        permissions=[("validate_commande","Peut valider une commande"), ("manage_commande","Peut gérer les commandes")]
    def save(self,*args,**kwargs):
        if not self.reference:
            self.reference=f"CMD-{self.date.year if self.date else 2026}-{Commande.objects.count()+1:04d}"
        super().save(*args,**kwargs)
    def __str__(self): return self.reference

class LigneCommande(models.Model):
    commande=models.ForeignKey(Commande,on_delete=models.CASCADE,related_name="lignes"); description=models.CharField(max_length=240); type_verre=models.ForeignKey(TypeVerre,null=True,blank=True,on_delete=models.PROTECT); epaisseur=models.ForeignKey(Epaisseur,null=True,blank=True,on_delete=models.PROTECT); longueur=models.PositiveIntegerField(null=True,blank=True); largeur=models.PositiveIntegerField(null=True,blank=True); quantite=models.PositiveIntegerField(default=1); decoupe=models.BooleanField(default=True); rabotage=models.BooleanField(default=False); percage=models.BooleanField(default=False); trempe=models.BooleanField(default=False); autres_prestations=models.CharField(max_length=240,blank=True)

class HistoriqueCommande(models.Model):
    commande=models.ForeignKey(Commande,on_delete=models.PROTECT,related_name="historique"); ancien_statut=models.CharField(max_length=20,blank=True); nouveau_statut=models.CharField(max_length=20); date=models.DateTimeField(auto_now_add=True); utilisateur=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.SET_NULL); commentaire=models.TextField(blank=True)
    class Meta: ordering=["-date"]
