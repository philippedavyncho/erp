from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase

from panneaux.models import Panneau
from types_verres.models import Epaisseur, Teinte, TypeVerre

from .models import MouvementStockGrandPanneau, PlanificationStock, StockGrandPanneau
from .services import StockInsuffisantError, annuler_planification, consommer_pour_planification, enregistrer_entree


class StockGrandPanneauServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("stockier", password="secret")
        self.user.user_permissions.add(Permission.objects.get(codename="view_stockgrandpanneau"))
        self.materiau = TypeVerre.objects.create(designation="Verre standard")
        self.epaisseur = Epaisseur.objects.create(valeur="4.00")
        self.teinte = Teinte.objects.create(designation="Clair")
        self.stock = StockGrandPanneau.objects.create(
            reference="GP-001", materiau=self.materiau, epaisseur=self.epaisseur,
            teinte=self.teinte, longueur=1000, largeur=800, quantite_en_stock=2,
        )

    def _panneau_utilise(self, reference="PLAN-TEST"):
        return Panneau.objects.create(
            reference=reference, longueur=1000, largeur=800, type_verre=self.materiau,
            epaisseur=self.epaisseur, teinte=self.teinte,
        )

    def test_decrements_stock_and_records_output_history(self):
        consommer_pour_planification(
            longueur=1000, largeur=800, materiau=self.materiau, epaisseur=self.epaisseur.valeur, teinte="Clair",
            panneau_utilise=self._panneau_utilise(), utilisateur=self.user,
        )
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantite_en_stock, 1)
        mouvement = MouvementStockGrandPanneau.objects.get()
        self.assertEqual(mouvement.type, MouvementStockGrandPanneau.Type.SORTIE)
        self.assertEqual(mouvement.quantite, 1)
        self.assertEqual(mouvement.origine, "Planification")
        self.assertEqual(mouvement.utilisateur, self.user)

    def test_reception_increases_stock_and_records_its_origin(self):
        enregistrer_entree(self.stock, 3, origine="Bon fournisseur BR-42", utilisateur=self.user)

        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantite_en_stock, 5)
        mouvement = MouvementStockGrandPanneau.objects.get()
        self.assertEqual(mouvement.type, MouvementStockGrandPanneau.Type.ENTREE)
        self.assertEqual(mouvement.quantite, 3)
        self.assertEqual(mouvement.origine, "Bon fournisseur BR-42")

    def test_cancellation_restores_stock_and_records_input_history(self):
        planification = consommer_pour_planification(
            longueur=1000, largeur=800, materiau=self.materiau, epaisseur=self.epaisseur.valeur, teinte="Clair",
            panneau_utilise=self._panneau_utilise(), utilisateur=self.user,
        )
        annuler_planification(planification, self.user)
        self.stock.refresh_from_db()
        planification.refresh_from_db()
        self.assertEqual(self.stock.quantite_en_stock, 2)
        self.assertEqual(planification.statut, PlanificationStock.Statut.ANNULEE)
        self.assertEqual(MouvementStockGrandPanneau.objects.filter(type="ENTREE", origine__startswith="Annulation").count(), 1)

    def test_refuses_when_stock_is_insufficient(self):
        self.stock.quantite_en_stock = 0
        self.stock.save()
        with self.assertRaisesRegex(StockInsuffisantError, "0 panneau"):
            consommer_pour_planification(
                longueur=1000, largeur=800, materiau=self.materiau, epaisseur=self.epaisseur.valeur, teinte="Clair",
                panneau_utilise=self._panneau_utilise(), utilisateur=self.user,
            )
        self.assertFalse(MouvementStockGrandPanneau.objects.exists())

    def test_history_screen_displays_stock_movements_and_can_filter_a_panel(self):
        mouvement = MouvementStockGrandPanneau.objects.create(
            type=MouvementStockGrandPanneau.Type.ENTREE, panneau=self.stock,
            quantite=2, origine="Réception", utilisateur=self.user,
        )
        self.client.force_login(self.user)

        response = self.client.get("/grands-panneaux/historique/", {"panneau": self.stock.pk})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mouvements des grands panneaux")
        self.assertContains(response, mouvement.origine)
        self.assertContains(response, self.stock.reference)

    def test_stock_url_rejects_authenticated_user_without_view_permission(self):
        other = get_user_model().objects.create_user("reception", password="secret")
        self.client.force_login(other)
        self.assertEqual(self.client.get("/grands-panneaux/").status_code, 403)
