from django.db.models.signals import post_save
from django.dispatch import receiver

from mouvements.models import Mouvement
from .models import Chute, MouvementChute


@receiver(post_save, sender=Chute)
def trace_creation_chute(sender, instance, created, **kwargs):
    """Trace les chutes générées automatiquement comme celles saisies manuellement."""
    if created:
        MouvementChute.objects.create(
            chute=instance,
            action=MouvementChute.Action.CREATION,
            nouveau_statut=instance.etat,
            nouvel_emplacement=instance.emplacement,
            nouvelles_dimensions=f"{instance.longueur} × {instance.largeur} mm",
        )
        Mouvement.objects.create(action="CREATION_CHUTE", objet=instance.numero)
