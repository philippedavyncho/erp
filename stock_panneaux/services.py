"""Point unique pour toutes les modifications du stock de grands panneaux."""
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .models import MouvementStockGrandPanneau, PlanificationStock, StockGrandPanneau


class StockInsuffisantError(ValueError):
    pass


@transaction.atomic
def enregistrer_entree(panneau, quantite, origine="Ajout manuel", utilisateur=None):
    if quantite <= 0:
        raise ValueError("La quantité doit être positive.")
    panneau = StockGrandPanneau.objects.select_for_update().get(pk=panneau.pk)
    panneau.quantite_en_stock = F("quantite_en_stock") + quantite
    panneau.save(update_fields=["quantite_en_stock", "date_modification"])
    MouvementStockGrandPanneau.objects.create(
        type=MouvementStockGrandPanneau.Type.ENTREE, panneau=panneau,
        quantite=quantite, origine=origine, utilisateur=utilisateur,
    )


@transaction.atomic
def consommer_pour_planification(*, longueur, largeur, materiau, epaisseur, teinte, panneau_utilise, utilisateur=None):
    """Décrémente une unité compatible et garde une trace de la planification."""
    panneaux = StockGrandPanneau.objects.select_for_update().filter(
        materiau=materiau, epaisseur__valeur=epaisseur,
        teinte__designation__iexact=teinte.strip(), longueur=longueur, largeur=largeur,
    ).order_by("reference")
    panneau_stock = panneaux.filter(quantite_en_stock__gte=1).first()
    if panneau_stock is None:
        disponible = sum(p.quantite_en_stock for p in panneaux)
        raise StockInsuffisantError(
            f"Stock insuffisant pour ce panneau : {disponible} panneau(x) disponible(s)."
        )
    panneau_stock.quantite_en_stock = F("quantite_en_stock") - 1
    panneau_stock.save(update_fields=["quantite_en_stock", "date_modification"])
    MouvementStockGrandPanneau.objects.create(
        type=MouvementStockGrandPanneau.Type.SORTIE, panneau=panneau_stock,
        quantite=1, origine="Planification", utilisateur=utilisateur,
    )
    return PlanificationStock.objects.create(
        panneau_stock=panneau_stock, panneau_utilise=panneau_utilise, utilisateur=utilisateur,
    )


@transaction.atomic
def consommer_pour_devis(panneau, quantite, reference_devis, utilisateur=None):
    """Enregistre la sortie de grands panneaux affectés à un devis validé."""
    if quantite <= 0:
        raise ValueError("La quantité de panneaux doit être positive.")
    panneau = StockGrandPanneau.objects.select_for_update().get(pk=panneau.pk)
    if panneau.quantite_en_stock < quantite:
        raise StockInsuffisantError(f"Stock insuffisant pour {panneau.reference} : {panneau.quantite_en_stock} panneau(x) disponible(s).")
    panneau.quantite_en_stock = F("quantite_en_stock") - quantite
    panneau.save(update_fields=["quantite_en_stock", "date_modification"])
    MouvementStockGrandPanneau.objects.create(type=MouvementStockGrandPanneau.Type.SORTIE, panneau=panneau, quantite=quantite, origine=f"Devis validé {reference_devis}", utilisateur=utilisateur)


@transaction.atomic
def annuler_planification(planification, utilisateur=None):
    """Restitue une seule fois les panneaux consommés par une planification."""
    planification = PlanificationStock.objects.select_for_update().select_related("panneau_stock").get(pk=planification.pk)
    if planification.statut == PlanificationStock.Statut.ANNULEE:
        raise ValueError("Cette planification est déjà annulée.")
    panneau = StockGrandPanneau.objects.select_for_update().get(pk=planification.panneau_stock_id)
    panneau.quantite_en_stock = F("quantite_en_stock") + planification.quantite
    panneau.save(update_fields=["quantite_en_stock", "date_modification"])
    planification.statut = PlanificationStock.Statut.ANNULEE
    planification.annule_le = timezone.now()
    planification.save(update_fields=["statut", "annule_le"])
    MouvementStockGrandPanneau.objects.create(
        type=MouvementStockGrandPanneau.Type.ENTREE, panneau=panneau,
        quantite=planification.quantite, origine="Annulation de planification", utilisateur=utilisateur,
    )
