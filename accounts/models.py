"""Groupes métier et leurs permissions Django natives."""
from django.contrib.auth.models import Group, Permission


def _permissions(*codes):
    """Return native Django permissions by their app_label.codename key."""
    result = []
    for code in codes:
        app_label, codename = code.split(".", 1)
        result.extend(Permission.objects.filter(content_type__app_label=app_label, codename=codename))
    return result

ROLES = ("ADMINISTRATEUR", "RESPONSABLE_COMMERCIAL", "RECEPTION", "RESPONSABLE_PRODUCTION", "MAGASINIER", "OPERATEUR_DECOUPE", "OPERATEUR_PRODUCTION", "CONTROLE_QUALITE", "DIRECTION")


def initialise_roles() -> None:
    for role in ROLES:
        group, _ = Group.objects.get_or_create(name=role)
        if role == "ADMINISTRATEUR":
            permissions = Permission.objects.all()
        elif role == "DIRECTION":
            permissions = Permission.objects.filter(codename__startswith="view_")
        elif role == "RESPONSABLE_COMMERCIAL":
            permissions = Permission.objects.filter(content_type__app_label__in=["clients", "commercial", "commandes"]).exclude(codename__startswith="delete_")
        elif role == "RECEPTION":
            permissions = Permission.objects.filter(content_type__app_label__in=["clients", "commercial"]).filter(codename__in=["view_client", "add_client", "change_client", "manage_client", "view_demandedevis", "add_demandedevis", "change_demandedevis", "view_devis", "add_devis", "change_devis"])
            permissions = list(permissions) + _permissions("commandes.view_commande")
        elif role == "MAGASINIER":
            permissions = Permission.objects.filter(content_type__app_label__in=["chutes", "stock_panneaux", "mouvements", "emplacements", "types_verres"]).exclude(codename__startswith="delete_")
        elif role == "OPERATEUR_DECOUPE":
            permissions = _permissions("decoupes.plan_cut", "chutes.view_chute", "production.view_ficheproduction", "production.view_pieceproduction", "production.view_etapeproduction")
        elif role == "OPERATEUR_PRODUCTION":
            permissions = _permissions("production.view_ficheproduction", "production.view_pieceproduction", "production.view_etapeproduction", "production.operate_production")
        elif role == "CONTROLE_QUALITE":
            permissions = _permissions("production.view_ficheproduction", "production.view_pieceproduction", "production.view_etapeproduction", "production.control_quality")
        else:
            permissions = Permission.objects.filter(content_type__app_label="production").exclude(codename__startswith="delete_")
            permissions = list(permissions) + _permissions(
                "commandes.view_commande", "decoupes.plan_cut", "chutes.view_chute",
                "stock_panneaux.view_stockgrandpanneau",
            )
        group.permissions.set(permissions)
