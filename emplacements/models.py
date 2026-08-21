from django.db import models
class Emplacement(models.Model):
    code = models.CharField(max_length=40, unique=True)
    chariot = models.CharField(max_length=50)
    niveau = models.PositiveSmallIntegerField()
    case = models.PositiveSmallIntegerField()
    description = models.TextField(blank=True)
    actif = models.BooleanField(default=True)
    class Meta: constraints = [models.UniqueConstraint(fields=["chariot", "niveau", "case"], name="emplacement_unique")]; ordering=["chariot","niveau","case"]
    def __str__(self): return self.code
