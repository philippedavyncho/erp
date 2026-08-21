from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from clients.models import Client
from commandes.models import Commande
from types_verres.models import TypeVerre
from commandes.services import transformer_devis
from .models import Devis, HistoriqueDevis, LigneDevis
from .services import changer_statut_devis

class CommercialWorkflowTests(TestCase):
    def setUp(self): self.user=get_user_model().objects.create_user("commercial"); self.client_obj=Client.objects.create(nom="Vitrerie test")
    def test_totals_and_single_transformation(self):
        devis=Devis.objects.create(client=self.client_obj,statut=Devis.Statut.ACCEPTE)
        LigneDevis.objects.create(devis=devis,description="Verre",quantite=2,prix_unitaire=Decimal("12.50")); devis.recalculer_totaux(); devis.refresh_from_db()
        self.assertEqual(devis.total_ttc,Decimal("30.00")); commande=transformer_devis(devis,self.user); self.assertEqual(commande.lignes.count(),1)
        with self.assertRaises(ValueError): transformer_devis(devis,self.user)

    def test_only_user_with_accept_permission_can_accept_and_it_is_traced(self):
        devis=Devis.objects.create(client=self.client_obj, statut=Devis.Statut.ENVOYE)
        self.user.user_permissions.add(Permission.objects.get(codename="accept_devis"))
        changer_statut_devis(devis, Devis.Statut.ACCEPTE, self.user)
        devis.refresh_from_db()
        self.assertEqual(devis.statut, Devis.Statut.ACCEPTE)
        self.assertEqual(HistoriqueDevis.objects.get(devis=devis).utilisateur, self.user)

    def test_glass_price_per_square_meter_is_applied_server_side(self):
        devis = Devis.objects.create(client=self.client_obj)
        verre = TypeVerre.objects.create(designation="Feuilleté 6 mm", prix_m2=Decimal("12500"))
        ligne = LigneDevis.objects.create(
            devis=devis, description="Vitrine", type_verre=verre,
            longueur=2000, largeur=1000, quantite=2, prix_unitaire=Decimal("1"),
        )
        ligne.refresh_from_db()
        self.assertEqual(ligne.prix_unitaire, Decimal("12500"))
        self.assertEqual(ligne.montant, Decimal("50000"))
