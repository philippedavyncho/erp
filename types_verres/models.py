from decimal import Decimal

from django.db import models

class NamedModel(models.Model):
    designation = models.CharField(max_length=100, unique=True)
    class Meta: abstract = True; ordering = ["designation"]
    def __str__(self): return self.designation
class TypeVerre(NamedModel):
    prix_m2 = models.DecimalField(
        "Prix au m² (FCFA)", max_digits=12, decimal_places=2,
        default=Decimal("0.00"), help_text="Tarif de référence en francs CFA pour un mètre carré.",
    )
class Teinte(NamedModel): pass
class Epaisseur(models.Model):
    valeur = models.DecimalField(max_digits=5, decimal_places=2, unique=True, help_text="mm")
    class Meta: ordering = ["valeur"]
    def __str__(self): return f"{self.valeur} mm"
