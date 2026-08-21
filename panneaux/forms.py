from django.forms import ModelForm
from .models import Panneau
class PanneauForm(ModelForm):
    class Meta: model=Panneau; fields="__all__"
