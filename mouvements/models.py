from django.conf import settings
from django.db import models
class Mouvement(models.Model):
    date=models.DateTimeField(auto_now_add=True); utilisateur=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.SET_NULL)
    action=models.CharField(max_length=40); objet=models.CharField(max_length=120); commentaire=models.TextField(blank=True)
    class Meta: ordering=["-date"]
    def __str__(self): return f"{self.action} — {self.objet}"
