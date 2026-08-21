from django.db.models.signals import post_save
from django.dispatch import receiver
from mouvements.models import Mouvement
from .models import Panneau


@receiver(post_save, sender=Panneau)
def trace_panneau(sender, instance, created, **kwargs):
    Mouvement.objects.create(action="ENTREE_PANNEAU" if created else "MODIFICATION_PANNEAU", objet=instance.reference)
