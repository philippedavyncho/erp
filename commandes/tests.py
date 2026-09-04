from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase

from clients.models import Client
from .models import Commande, LigneCommande
from .services import changer_statut


class LivraisonWorkflowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("responsable")
        self.user.user_permissions.add(Permission.objects.get(codename="manage_commande"), Permission.objects.get(codename="view_commande"))
        self.commande = Commande.objects.create(client=Client.objects.create(nom="Client"), statut=Commande.Statut.TERMINEE)
        LigneCommande.objects.create(commande=self.commande, description="Vitre", longueur=800, largeur=600, quantite=2)

    def test_ready_order_has_delivery_note_and_can_be_delivered(self):
        changer_statut(self.commande, Commande.Statut.PRETE, self.user)
        self.commande.refresh_from_db()
        self.assertEqual(self.commande.statut, Commande.Statut.PRETE)
        self.client.force_login(self.user)
        response = self.client.get(f"/commandes/{self.commande.pk}/bon-livraison/")
        self.assertContains(response, "BON DE LIVRAISON")
        changer_statut(self.commande, Commande.Statut.LIVREE, self.user)
        self.commande.refresh_from_db()
        self.assertEqual(self.commande.statut, Commande.Statut.LIVREE)
