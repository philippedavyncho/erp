from decimal import Decimal
from django import forms
from panneaux.models import Panneau
from chutes.models import Chute
from emplacements.models import Emplacement
from types_verres.models import TypeVerre


class DecoupeForm(forms.Form):
    panneau = forms.ModelChoiceField(queryset=Panneau.objects.filter(statut="DISPONIBLE"), required=False)
    chute = forms.ModelChoiceField(queryset=Chute.objects.filter(etat="DISPONIBLE"), required=False)
    longueur = forms.IntegerField(min_value=100)
    largeur = forms.IntegerField(min_value=100)
    emplacement = forms.ModelChoiceField(queryset=Emplacement.objects.filter(actif=True), label="Emplacement des nouvelles chutes")
    decoupes_supplementaires = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 4}))

    def clean(self):
        data = super().clean()
        if bool(data.get("panneau")) == bool(data.get("chute")):
            raise forms.ValidationError("Selectionnez un panneau ou une chute.")
        lignes = [(data.get("longueur"), data.get("largeur"))]
        for ligne in data.get("decoupes_supplementaires", "").splitlines():
            if not ligne.strip():
                continue
            morceaux = ligne.lower().replace("×", "x").split("x")
            if len(morceaux) != 2 or not all(x.strip().isdigit() for x in morceaux):
                raise forms.ValidationError("Utilisez le format longueur x largeur.")
            lignes.append((int(morceaux[0]), int(morceaux[1])))
        data["lignes"] = lignes
        return data


class PlanificationForm(forms.Form):
    materiau = forms.ModelChoiceField(queryset=TypeVerre.objects.all(), required=False, label="Matériau", help_text="Laissez vide pour le verre standard.")
    longueur_panneau = forms.IntegerField(min_value=100, label="Longueur du panneau (mm)")
    largeur_panneau = forms.IntegerField(min_value=100, label="Largeur du panneau (mm)")
    epaisseur = forms.DecimalField(min_value=Decimal("0.01"), max_digits=5, decimal_places=2, label="Epaisseur (mm)")
    teinte = forms.CharField(max_length=100, label="Couleur")
    emplacement = forms.ModelChoiceField(
        queryset=Emplacement.objects.filter(actif=True),
        label="Emplacement des chutes",
        help_text="Toutes les chutes créées par ce plan seront rangées à cet emplacement.",
    )
    decoupes = forms.CharField(widget=forms.Textarea(attrs={"rows": 7, "placeholder": "1800 x 900\n1500 x 600"}), label="Dimensions a decouper", help_text="Une découpe par ligne, au format longueur x largeur (mm).")

    def clean_decoupes(self):
        result = []
        for ligne in self.cleaned_data["decoupes"].splitlines():
            morceaux = ligne.lower().replace("×", "x").split("x")
            if len(morceaux) != 2 or not all(item.strip().isdigit() and int(item.strip()) >= 100 for item in morceaux):
                raise forms.ValidationError("Chaque ligne doit être au format 1800 x 900 (minimum 100 mm).")
            result.append((int(morceaux[0]), int(morceaux[1])))
        if not result:
            raise forms.ValidationError("Saisissez au moins une découpe.")
        return result
