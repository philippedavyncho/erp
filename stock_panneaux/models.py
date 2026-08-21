from django.conf import settings
from django.db import models

from panneaux.models import Panneau
from types_verres.models import Epaisseur, Teinte, TypeVerre


class StockGrandPanneau(models.Model):
    """Une référence de grand panneau et la quantité physique disponible."""

    reference = models.CharField(max_length=80, unique=True)
    materiau = models.ForeignKey(TypeVerre, on_delete=models.PROTECT, verbose_name="Matériau")
    epaisseur = models.ForeignKey(Epaisseur, on_delete=models.PROTECT)
    teinte = models.ForeignKey(Teinte, on_delete=models.PROTECT, verbose_name="Couleur")
    longueur = models.PositiveIntegerField(help_text="mm")
    largeur = models.PositiveIntegerField(help_text="mm")
    quantite_en_stock = models.PositiveIntegerField(default=0)
    quantite_minimum = models.PositiveIntegerField(default=0)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["reference"]
        verbose_name = "stock de grand panneau"
        verbose_name_plural = "stocks de grands panneaux"
        permissions = [("manage_stock", "Peut gérer le stock de panneaux")]

    def __str__(self):
        return self.reference

    @property
    def sous_seuil(self):
        return self.quantite_en_stock < self.quantite_minimum


class MouvementStockGrandPanneau(models.Model):
    class Type(models.TextChoices):
        ENTREE = "ENTREE", "Entrée"
        SORTIE = "SORTIE", "Sortie"

    type = models.CharField(max_length=10, choices=Type.choices)
    panneau = models.ForeignKey(StockGrandPanneau, on_delete=models.PROTECT, related_name="mouvements")
    quantite = models.PositiveIntegerField()
    origine = models.CharField(max_length=120)
    date = models.DateTimeField(auto_now_add=True)
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ["-date"]


class PlanificationStock(models.Model):
    """Lien auditable entre un panneau consommé et la planification réalisée."""

    class Statut(models.TextChoices):
        VALIDEE = "VALIDEE", "Validée"
        ANNULEE = "ANNULEE", "Annulée"

    panneau_stock = models.ForeignKey(StockGrandPanneau, on_delete=models.PROTECT, related_name="planifications")
    panneau_utilise = models.OneToOneField(Panneau, on_delete=models.PROTECT, related_name="consommation_stock")
    quantite = models.PositiveIntegerField(default=1)
    statut = models.CharField(max_length=10, choices=Statut.choices, default=Statut.VALIDEE)
    cree_le = models.DateTimeField(auto_now_add=True)
    annule_le = models.DateTimeField(null=True, blank=True)
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
