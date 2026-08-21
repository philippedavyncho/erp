from django import forms
from .models import DemandeDevis, Devis, LigneDevis
class DemandeDevisForm(forms.ModelForm):
    class Meta: model=DemandeDevis; fields=("client","description","produits","dimensions","type_verre","epaisseur","quantite","prestations","statut","commentaire")
class DevisForm(forms.ModelForm):
    class Meta: model=Devis; fields=("client","demande","validite","remise","tva_taux","observations")
class LigneDevisForm(forms.ModelForm):
    class Meta:
        model=LigneDevis
        exclude=("devis","prix_unitaire","montant")
