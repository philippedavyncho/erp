from decimal import Decimal
from django.db import models
from types_verres.models import TypeVerre, Epaisseur, Teinte
class Panneau(models.Model):
    class Statut(models.TextChoices): DISPONIBLE="DISPONIBLE", "Disponible"; EPUISE="EPUISE", "Épuisé"; ARCHIVE="ARCHIVE", "Archivé"
    reference = models.CharField(max_length=80, unique=True)
    longueur = models.PositiveIntegerField(help_text="mm"); largeur = models.PositiveIntegerField(help_text="mm")
    surface = models.DecimalField(max_digits=12, decimal_places=4, editable=False, default=0)
    type_verre=models.ForeignKey(TypeVerre,on_delete=models.PROTECT); epaisseur=models.ForeignKey(Epaisseur,on_delete=models.PROTECT); teinte=models.ForeignKey(Teinte,on_delete=models.PROTECT)
    date_entree=models.DateField(auto_now_add=True); statut=models.CharField(max_length=12,choices=Statut.choices,default=Statut.DISPONIBLE)
    class Meta: ordering=["-date_entree"]
    def save(self,*args,**kwargs): self.surface=(Decimal(self.longueur)*Decimal(self.largeur)/Decimal(1_000_000)).quantize(Decimal(".0001")); super().save(*args,**kwargs)
    def __str__(self): return self.reference
