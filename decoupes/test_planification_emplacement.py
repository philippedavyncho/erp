from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase

from chutes.models import Chute
from emplacements.models import Emplacement
from stock_panneaux.models import StockGrandPanneau
from types_verres.models import Epaisseur, Teinte, TypeVerre


class PlanificationEmplacementTests(TestCase):
    def test_validation_stores_offcuts_at_selected_location(self):
        user = get_user_model().objects.create_user("operateur", password="secret")
        user.user_permissions.add(Permission.objects.get(codename="plan_cut"))
        emplacement = Emplacement.objects.create(code="B-02-03", chariot="B", niveau=2, case=3)
        materiau = TypeVerre.objects.create(designation="Verre standard")
        epaisseur = Epaisseur.objects.create(valeur="4.00")
        teinte = Teinte.objects.create(designation="Clair")
        StockGrandPanneau.objects.create(
            reference="GP-1000-800", materiau=materiau, epaisseur=epaisseur, teinte=teinte,
            longueur=1000, largeur=800, quantite_en_stock=1,
        )
        self.client.force_login(user)

        response = self.client.post("/decoupes/", {
            "longueur_panneau": 1000,
            "largeur_panneau": 800,
            "epaisseur": "4.00",
            "teinte": "Clair",
            "emplacement": emplacement.pk,
            "decoupes": "600 x 500",
            "action": "valider",
        })

        self.assertRedirects(response, "/stockage/")
        self.assertTrue(Chute.objects.filter(emplacement=emplacement).exists())
