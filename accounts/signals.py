from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import initialise_roles
@receiver(post_migrate)
def create_roles(**kwargs): initialise_roles()
