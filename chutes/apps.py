from django.apps import AppConfig


class ChutesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "chutes"

    def ready(self):
        from . import signals  # noqa: F401
