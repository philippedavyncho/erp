from django.conf import settings
from django.db import models
from panneaux.models import Panneau
from chutes.models import Chute
class Decoupe(models.Model):
    panneau=models.ForeignKey(Panneau,null=True,blank=True,on_delete=models.PROTECT,related_name="decoupes")
    chute_source=models.ForeignKey(Chute,null=True,blank=True,on_delete=models.PROTECT,related_name="decoupes")
    longueur=models.PositiveIntegerField(); largeur=models.PositiveIntegerField(); cree_le=models.DateTimeField(auto_now_add=True); utilisateur=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.SET_NULL)
    class Meta:
        ordering=["-cree_le"]
        permissions=[("plan_cut", "Peut planifier et valider une découpe")]
    def __str__(self): return f"{self.longueur} × {self.largeur} mm"
