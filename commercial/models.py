from decimal import Decimal
from django.conf import settings
from django.db import models
from clients.models import Client
from types_verres.models import Epaisseur, TypeVerre


class DemandeDevis(models.Model):
    class Statut(models.TextChoices):
        BROUILLON="BROUILLON", "Brouillon"; EN_ETUDE="EN_ETUDE", "En étude"; DEVIS_EN_PREPARATION="DEVIS_EN_PREPARATION", "Devis en préparation"; DEVIS_ENVOYE="DEVIS_ENVOYE", "Devis envoyé"; TERMINE="TERMINE", "Terminée"
    class Priorite(models.TextChoices):
        NORMALE="NORMALE", "Normale"; HAUTE="HAUTE", "Haute"; URGENTE="URGENTE", "Urgente"
    client=models.ForeignKey(Client,on_delete=models.PROTECT,related_name="demandes_devis")
    titre=models.CharField(max_length=160, blank=True, help_text="Ex. Vitrine boutique, remplacement de baie, garde-corps")
    description=models.TextField(); produits=models.TextField(blank=True)
    dimensions=models.CharField(max_length=120, blank=True, help_text="Ex. 1200 × 800 mm")
    type_verre=models.ForeignKey(TypeVerre, null=True, blank=True, on_delete=models.PROTECT)
    epaisseur=models.ForeignKey(Epaisseur, null=True, blank=True, on_delete=models.PROTECT)
    quantite=models.PositiveIntegerField(default=1)
    prestations=models.TextField(blank=True)
    chantier_adresse=models.TextField(blank=True)
    contact_chantier=models.CharField(max_length=120, blank=True)
    telephone_chantier=models.CharField(max_length=40, blank=True)
    date_souhaitee=models.DateField(null=True, blank=True)
    priorite=models.CharField(max_length=10, choices=Priorite.choices, default=Priorite.NORMALE)
    pose_souhaitee=models.BooleanField(default=False)
    prise_mesures_souhaitee=models.BooleanField(default=False)
    statut=models.CharField(max_length=24,choices=Statut.choices,default=Statut.BROUILLON)
    cree_le=models.DateTimeField(auto_now_add=True); cree_par=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.SET_NULL); commentaire=models.TextField(blank=True)

    class Meta: ordering=["-cree_le"]

class Devis(models.Model):
    class Statut(models.TextChoices):
        BROUILLON="BROUILLON", "Brouillon"; ENVOYE="ENVOYE", "Envoyé"; EN_ATTENTE="EN_ATTENTE", "En attente"; ACCEPTE="ACCEPTE", "Accepté"; REFUSE="REFUSE", "Refusé"; EXPIRE="EXPIRE", "Expiré"; ANNULE="ANNULE", "Annulé"
    reference=models.CharField(max_length=24,unique=True,blank=True)
    client=models.ForeignKey(Client,on_delete=models.PROTECT,related_name="devis")
    demande=models.ForeignKey(DemandeDevis,null=True,blank=True,on_delete=models.SET_NULL,related_name="devis")
    statut=models.CharField(max_length=16,choices=Statut.choices,default=Statut.BROUILLON)
    date=models.DateField(auto_now_add=True); validite=models.DateField(null=True,blank=True)
    chantier_adresse=models.TextField(blank=True, help_text="Adresse de pose ou de livraison si différente du client")
    chantier_contact=models.CharField(max_length=120, blank=True)
    chantier_telephone=models.CharField(max_length=40, blank=True)
    delai_fabrication=models.CharField(max_length=120, blank=True, help_text="Ex. 7 à 10 jours ouvrés après validation")
    acompte_taux=models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("50.00"))
    conditions_paiement=models.TextField(blank=True, default="50 % à la commande, solde à la livraison.")
    pose_incluse=models.BooleanField(default=False)
    prise_mesures_validee=models.BooleanField(default=False, help_text="Dimensions relevées et validées sur site")
    remise=models.DecimalField(max_digits=12,decimal_places=2,default=0); tva_taux=models.DecimalField(max_digits=5,decimal_places=2,default=Decimal("20.00"))
    sous_total=models.DecimalField(max_digits=12,decimal_places=2,default=0,editable=False); total_ht=models.DecimalField(max_digits=12,decimal_places=2,default=0,editable=False); total_ttc=models.DecimalField(max_digits=12,decimal_places=2,default=0,editable=False)
    observations=models.TextField(blank=True); cree_par=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.SET_NULL)

    class Meta:
        ordering=["-date", "-pk"]
        permissions=[("send_devis", "Peut envoyer un devis"), ("accept_devis", "Peut accepter un devis"), ("refuse_devis", "Peut refuser un devis"), ("cancel_devis", "Peut annuler un devis"), ("transform_devis", "Peut transformer un devis en commande")]

    def save(self,*args,**kwargs):
        if not self.reference:
            last=Devis.objects.filter(reference__startswith=f"DEV-{self.date.year if self.date else 2026}-").count()+1
            self.reference=f"DEV-{self.date.year if self.date else 2026}-{last:04d}"
        super().save(*args,**kwargs)

    def recalculer_totaux(self):
        subtotal=sum((line.montant for line in self.lignes.all()), Decimal())
        self.sous_total=subtotal; self.total_ht=max(subtotal-self.remise, Decimal()); self.total_ttc=self.total_ht*(Decimal(1)+self.tva_taux/100)
        self.save(update_fields=["sous_total","total_ht","total_ttc"])

class LigneDevis(models.Model):
    devis=models.ForeignKey(Devis,on_delete=models.CASCADE,related_name="lignes")
    description=models.CharField(max_length=240); type_verre=models.ForeignKey(TypeVerre,null=True,blank=True,on_delete=models.PROTECT); epaisseur=models.ForeignKey(Epaisseur,null=True,blank=True,on_delete=models.PROTECT)
    longueur=models.PositiveIntegerField(null=True,blank=True); largeur=models.PositiveIntegerField(null=True,blank=True); quantite=models.PositiveIntegerField(default=1); prix_unitaire=models.DecimalField("Prix au m² (FCFA)",max_digits=12,decimal_places=2,default=0,editable=False)
    decoupe=models.BooleanField(default=True); rabotage=models.BooleanField(default=False); percage=models.BooleanField(default=False); trempe=models.BooleanField(default=False); autres_prestations=models.CharField(max_length=240,blank=True)
    prix_prestations=models.DecimalField("Forfait prestations HT (FCFA)",max_digits=12,decimal_places=2,default=0)
    montant=models.DecimalField(max_digits=12,decimal_places=2,editable=False,default=0)
    panneau_stock=models.ForeignKey("stock_panneaux.StockGrandPanneau",null=True,blank=True,on_delete=models.PROTECT,related_name="lignes_devis")
    chute_stock=models.ForeignKey("chutes.Chute",null=True,blank=True,on_delete=models.PROTECT,related_name="lignes_devis")
    @property
    def surface_unitaire_m2(self):
        if not self.longueur or not self.largeur:
            return Decimal("0")
        return (Decimal(self.longueur) * Decimal(self.largeur) / Decimal("1000000")).quantize(Decimal("0.0001"))

    def save(self,*args,**kwargs):
        # Le tarif est toujours lu depuis le type de verre : aucune valeur navigateur
        # ne peut modifier le prix facturé d'une ligne.
        if self.type_verre_id:
            self.prix_unitaire = self.type_verre.prix_m2
        if self.type_verre_id and self.longueur and self.largeur:
            self.montant = (self.surface_unitaire_m2 * self.quantite * self.prix_unitaire + self.prix_prestations).quantize(Decimal("0.01"))
        else:
            # Compatibilité des anciennes lignes qui ne possèdent pas encore de dimensions.
            self.montant = self.quantite * self.prix_unitaire + self.prix_prestations
        super().save(*args,**kwargs)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.panneau_stock_id and self.chute_stock_id:
            raise ValidationError("Choisissez soit un grand panneau, soit une chute.")


class HistoriqueDevis(models.Model):
    devis=models.ForeignKey(Devis,on_delete=models.PROTECT,related_name="historique")
    ancien_statut=models.CharField(max_length=16,blank=True)
    nouveau_statut=models.CharField(max_length=16)
    date=models.DateTimeField(auto_now_add=True)
    utilisateur=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.SET_NULL)
    commentaire=models.TextField(blank=True)

    class Meta:
        ordering=["-date", "-pk"]
