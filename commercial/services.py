from django.core.exceptions import PermissionDenied
from django.db import transaction

from .models import Devis, HistoriqueDevis


STATUTS_AUTORISES = {
    Devis.Statut.ENVOYE: {Devis.Statut.BROUILLON, Devis.Statut.EN_ATTENTE},
    Devis.Statut.ACCEPTE: {Devis.Statut.ENVOYE, Devis.Statut.EN_ATTENTE},
    Devis.Statut.REFUSE: {Devis.Statut.ENVOYE, Devis.Statut.EN_ATTENTE},
    Devis.Statut.ANNULE: {Devis.Statut.BROUILLON, Devis.Statut.ENVOYE, Devis.Statut.EN_ATTENTE},
}
PERMISSION_PAR_STATUT = {
    Devis.Statut.ENVOYE: "commercial.send_devis",
    Devis.Statut.ACCEPTE: "commercial.accept_devis",
    Devis.Statut.REFUSE: "commercial.refuse_devis",
    Devis.Statut.ANNULE: "commercial.cancel_devis",
}


@transaction.atomic
def changer_statut_devis(devis, nouveau_statut, utilisateur, commentaire=""):
    """Apply a permitted business transition and leave an immutable audit entry."""
    permission = PERMISSION_PAR_STATUT.get(nouveau_statut)
    if permission is None or not utilisateur.has_perm(permission):
        raise PermissionDenied
    devis = Devis.objects.select_for_update().get(pk=devis.pk)
    if devis.statut not in STATUTS_AUTORISES[nouveau_statut]:
        raise ValueError("Cette transition de statut n'est pas autorisée.")
    ancien_statut = devis.statut
    devis.statut = nouveau_statut
    devis.save(update_fields=["statut"])
    HistoriqueDevis.objects.create(devis=devis, ancien_statut=ancien_statut, nouveau_statut=nouveau_statut, utilisateur=utilisateur, commentaire=commentaire)
    return devis
