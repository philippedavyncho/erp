from django.contrib.auth import get_user_model
from django.test import TestCase
from clients.models import Client
from commandes.models import Commande, LigneCommande
from .services import creer_fiche
class ProductionTests(TestCase):
    def test_validated_order_creates_production_steps(self):
        user=get_user_model().objects.create_user("prod"); order=Commande.objects.create(client=Client.objects.create(nom="Client"),statut=Commande.Statut.VALIDEE); LigneCommande.objects.create(commande=order,description="Pièce",longueur=1000,largeur=500,quantite=1,rabotage=True)
        fiche=creer_fiche(order,user); self.assertEqual(fiche.pieces.count(),1); self.assertEqual(fiche.pieces.first().etapes.count(),3)
