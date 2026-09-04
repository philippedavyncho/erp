from django import forms
from .models import DemandeDevis, Devis, LigneDevis
class DemandeDevisForm(forms.ModelForm):
    class Meta:
        model=DemandeDevis
        fields=("client","titre","description","produits","dimensions","type_verre","epaisseur","quantite","prestations","chantier_adresse","contact_chantier","telephone_chantier","date_souhaitee","priorite","pose_souhaitee","prise_mesures_souhaitee","commentaire")
        widgets={"date_souhaitee": forms.DateInput(attrs={"type": "date"})}
class DevisForm(forms.ModelForm):
    class Meta: model=Devis; fields=("client","demande","validite","chantier_adresse","chantier_contact","chantier_telephone","delai_fabrication","acompte_taux","conditions_paiement","pose_incluse","prise_mesures_validee","remise","tva_taux","observations")
class LigneDevisForm(forms.ModelForm):
    class Meta:
        model=LigneDevis
        exclude=("devis","prix_unitaire","montant")
        widgets={"panneau_stock":forms.Select(attrs={"class":"form-select"}),"chute_stock":forms.Select(attrs={"class":"form-select"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from chutes.models import Chute
        from stock_panneaux.models import StockGrandPanneau
        self.fields["panneau_stock"].queryset = StockGrandPanneau.objects.filter(quantite_en_stock__gt=0).order_by("reference")
        self.fields["panneau_stock"].label = "Grand panneau suggéré pour l'atelier (facultatif)"
        self.fields["chute_stock"].queryset = Chute.objects.filter(etat=Chute.Etat.DISPONIBLE).order_by("numero")
        self.fields["chute_stock"].label = "Chute suggérée pour l'atelier (facultatif)"

    def clean(self):
        cleaned=super().clean()
        panneau, chute = cleaned.get("panneau_stock"), cleaned.get("chute_stock")
        if panneau and chute:
            raise forms.ValidationError("Choisissez une seule source de matière par ligne.")
        if chute and cleaned.get("quantite",1) != 1:
            self.add_error("quantite","Une chute ne peut être affectée qu'à une seule pièce.")
        source = panneau or chute
        if source:
            longueur, largeur = cleaned.get("longueur"), cleaned.get("largeur")
            if longueur and largeur and not ((source.longueur >= longueur and source.largeur >= largeur) or (source.longueur >= largeur and source.largeur >= longueur)):
                raise forms.ValidationError("La matière sélectionnée ne permet pas cette découpe, même après rotation.")
            materiau = getattr(source, "materiau", None) or source.type_verre
            if cleaned.get("type_verre") and materiau != cleaned["type_verre"]:
                self.add_error("type_verre", "Le type de verre ne correspond pas à la matière sélectionnée.")
            if cleaned.get("epaisseur") and source.epaisseur != cleaned["epaisseur"]:
                self.add_error("epaisseur", "L'épaisseur ne correspond pas à la matière sélectionnée.")
        if panneau and panneau.quantite_en_stock < cleaned.get("quantite", 1):
            self.add_error("panneau_stock", "La quantité disponible de ce panneau est insuffisante.")
        return cleaned
