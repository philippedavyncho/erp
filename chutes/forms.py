from django import forms
from emplacements.models import Emplacement
from types_verres.models import Epaisseur, Teinte
from .models import Chute, MouvementChute


class ChuteForm(forms.ModelForm):
    class Meta:
        model = Chute
        exclude = ("numero", "surface", "code_qr", "date_creation")


class RechercheChuteForm(forms.Form):
    """The four criteria used to locate a reusable offcut."""
    longueur = forms.IntegerField(min_value=100, label="Longueur (mm)")
    largeur = forms.IntegerField(min_value=100, label="Largeur (mm)")
    epaisseur = forms.ModelChoiceField(queryset=Epaisseur.objects.all(), label="Epaisseur")
    teinte = forms.ModelChoiceField(queryset=Teinte.objects.all(), label="Couleur")


class DeplacementChuteForm(forms.Form):
    emplacement = forms.ModelChoiceField(queryset=Emplacement.objects.filter(actif=True), label="Nouvel emplacement")
    commentaire = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))


class CorrectionChuteForm(forms.ModelForm):
    commentaire = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}), label="Motif / commentaire")

    class Meta:
        model = Chute
        fields = ("longueur", "largeur", "type_verre", "epaisseur", "teinte", "emplacement")


class ReservationChuteForm(forms.Form):
    reference = forms.CharField(max_length=120, label="Commande, production ou plan")
    commentaire = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))


class ConfirmationChuteForm(forms.Form):
    commentaire = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))


class RebutChuteForm(ConfirmationChuteForm):
    motif = forms.ChoiceField(choices=MouvementChute.MotifRebut.choices, label="Motif du rebut")
