from django import forms

from .models import StockGrandPanneau


class StockGrandPanneauForm(forms.ModelForm):
    class Meta:
        model = StockGrandPanneau
        fields = (
            "reference", "materiau", "epaisseur", "teinte", "longueur", "largeur",
            "quantite_en_stock", "quantite_minimum",
        )


class ReceptionStockForm(forms.Form):
    """Réception d'un complément de stock, sans modifier la fiche article."""

    quantite = forms.IntegerField(min_value=1, label="Quantité reçue")
    origine = forms.CharField(
        max_length=120,
        label="Origine / bon de réception",
        help_text="Ex. : fournisseur, numéro de bon ou inventaire.",
    )
