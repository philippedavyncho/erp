from django.db import transaction
from commercial.models import Devis
from .models import Commande, HistoriqueCommande, LigneCommande
@transaction.atomic
def transformer_devis(devis,user):
    devis=Devis.objects.select_for_update().get(pk=devis.pk)
    if devis.statut!=Devis.Statut.ACCEPTE: raise ValueError("Seul un devis accepté peut devenir une commande.")
    if hasattr(devis,"commande"): raise ValueError("Une commande existe déjà pour ce devis.")
    commande=Commande.objects.create(client=devis.client,devis=devis,cree_par=user,commentaire=devis.observations)
    LigneCommande.objects.bulk_create([LigneCommande(commande=commande,description=l.description,type_verre=l.type_verre,epaisseur=l.epaisseur,longueur=l.longueur,largeur=l.largeur,quantite=l.quantite,decoupe=l.decoupe,rabotage=l.rabotage,percage=l.percage,trempe=l.trempe,autres_prestations=l.autres_prestations) for l in devis.lignes.all()])
    HistoriqueCommande.objects.create(commande=commande,nouveau_statut=commande.statut,utilisateur=user,commentaire=f"Créée depuis {devis.reference}")
    return commande
@transaction.atomic
def changer_statut(commande,statut,user,commentaire=""):
    commande=Commande.objects.select_for_update().get(pk=commande.pk)
    transitions = {
        Commande.Statut.VALIDEE: {Commande.Statut.NOUVELLE},
        Commande.Statut.EN_PREPARATION: {Commande.Statut.VALIDEE},
        Commande.Statut.EN_PRODUCTION: {Commande.Statut.EN_PREPARATION},
        Commande.Statut.TERMINEE: {Commande.Statut.EN_PRODUCTION},
        Commande.Statut.PRETE: {Commande.Statut.TERMINEE},
        Commande.Statut.LIVREE: {Commande.Statut.PRETE},
        Commande.Statut.ANNULEE: {Commande.Statut.NOUVELLE, Commande.Statut.VALIDEE},
    }
    if statut not in transitions or commande.statut not in transitions[statut]:
        raise ValueError("Transition de commande non autorisée.")
    ancien=commande.statut
    commande.statut=statut
    if statut==Commande.Statut.VALIDEE:
        commande.valide_par=user
    commande.save()
    HistoriqueCommande.objects.create(commande=commande,ancien_statut=ancien,nouveau_statut=statut,utilisateur=user,commentaire=commentaire)
    return commande
