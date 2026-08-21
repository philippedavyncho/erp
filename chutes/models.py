from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils.crypto import get_random_string

from emplacements.models import Emplacement
from types_verres.models import Epaisseur, Teinte, TypeVerre


class Chute(models.Model):
    class Etat(models.TextChoices):
        DISPONIBLE = "DISPONIBLE", "Disponible"
        RESERVEE = "RESERVEE", "Réservée"
        UTILISEE = "UTILISEE", "Utilisée"
        REBUT = "REBUT", "Rebut"

    numero = models.CharField(max_length=32, unique=True, blank=True)
    longueur = models.PositiveIntegerField()
    largeur = models.PositiveIntegerField()
    surface = models.DecimalField(max_digits=12, decimal_places=4, editable=False, default=0)
    type_verre = models.ForeignKey(TypeVerre, on_delete=models.PROTECT)
    epaisseur = models.ForeignKey(Epaisseur, on_delete=models.PROTECT)
    teinte = models.ForeignKey(Teinte, on_delete=models.PROTECT)
    emplacement = models.ForeignKey(Emplacement, on_delete=models.PROTECT)
    date_creation = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)
    modifie_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="chutes_modifiees")
    origine = models.CharField(max_length=120, blank=True)
    etat = models.CharField(max_length=12, choices=Etat.choices, default=Etat.DISPONIBLE)
    reservation_reference = models.CharField(max_length=120, blank=True)
    code_qr = models.CharField(max_length=128, unique=True, blank=True)

    class Meta:
        ordering = ["-date_creation"]
        permissions = [
            ("move_chute", "Peut déplacer une chute"),
            ("correct_chute", "Peut corriger une chute"),
            ("reserve_chute", "Peut réserver une chute"),
            ("use_chute", "Peut utiliser une chute"),
            ("discard_chute", "Peut mettre une chute au rebut"),
            ("view_chute_history", "Peut consulter l'historique des chutes"),
        ]

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = f"CH-{get_random_string(8).upper()}"
        if not self.code_qr:
            self.code_qr = f"verre:{self.numero}"
        self.surface = (Decimal(self.longueur) * Decimal(self.largeur) / Decimal(1_000_000)).quantize(Decimal(".0001"))
        super().save(*args, **kwargs)

    def __str__(self):
        return self.numero


class MouvementChute(models.Model):
    class Action(models.TextChoices):
        CREATION = "CREATION", "Création"
        DEPLACEMENT = "DEPLACEMENT", "Déplacement"
        CORRECTION = "CORRECTION", "Correction"
        RESERVATION = "RESERVATION", "Réservation"
        ANNULATION_RESERVATION = "ANNULATION_RESERVATION", "Annulation réservation"
        UTILISATION = "UTILISATION", "Utilisation"
        REBUT = "REBUT", "Mise au rebut"

    class MotifRebut(models.TextChoices):
        CASSE = "CASSE", "Cassé"
        RAYURE = "RAYURE", "Rayure"
        DEFAUT = "DEFAUT", "Défaut"
        DIMENSION_INCORRECTE = "DIMENSION_INCORRECTE", "Dimension incorrecte"
        DETERIORATION = "DETERIORATION", "Détérioration"
        AUTRE = "AUTRE", "Autre"

    chute = models.ForeignKey(Chute, on_delete=models.PROTECT, related_name="historique")
    action = models.CharField(max_length=24, choices=Action.choices)
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    date = models.DateTimeField(auto_now_add=True)
    ancien_statut = models.CharField(max_length=12, blank=True)
    nouveau_statut = models.CharField(max_length=12, blank=True)
    ancien_emplacement = models.ForeignKey(Emplacement, null=True, blank=True, on_delete=models.PROTECT, related_name="mouvements_chutes_depart")
    nouvel_emplacement = models.ForeignKey(Emplacement, null=True, blank=True, on_delete=models.PROTECT, related_name="mouvements_chutes_arrivee")
    anciennes_dimensions = models.CharField(max_length=40, blank=True)
    nouvelles_dimensions = models.CharField(max_length=40, blank=True)
    motif = models.CharField(max_length=32, choices=MotifRebut.choices, blank=True)
    commentaire = models.TextField(blank=True)

    class Meta:
        ordering = ["-date", "-pk"]
        permissions = []

    def __str__(self):
        return f"{self.get_action_display()} — {self.chute.numero}"
