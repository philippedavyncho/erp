from django.conf import settings
from django.db import models


class Client(models.Model):
    reference = models.CharField(max_length=24, unique=True, blank=True)
    nom = models.CharField(max_length=160)
    contact = models.CharField(max_length=120, blank=True)
    telephone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    adresse = models.TextField(blank=True)
    ville = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    cree_le = models.DateTimeField(auto_now_add=True)
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ["nom"]
        permissions = [("manage_client", "Peut gérer les clients")]

    def save(self, *args, **kwargs):
        if not self.reference:
            dernier = Client.objects.order_by("-pk").values_list("pk", flat=True).first() or 0
            self.reference = f"CLI-{dernier + 1:05d}"
        super().save(*args, **kwargs)

    def __str__(self): return f"{self.reference} — {self.nom}"
