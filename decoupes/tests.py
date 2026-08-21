from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import SimpleTestCase, TestCase
from chutes.models import Chute
from emplacements.models import Emplacement
from types_verres.models import Epaisseur, Teinte, TypeVerre
from .models import Decoupe
from .services import Rectangle, compatibles, leftovers, planifier_panneau
class DecoupeEngineTests(SimpleTestCase):
    def test_discards_small_waste(self):
        self.assertEqual(leftovers(Rectangle(1000, 800), Rectangle(950, 800)), [])
    def test_creates_valid_guillotine_remainder(self):
        self.assertEqual(leftovers(Rectangle(1000, 800), Rectangle(600, 500)), [Rectangle(400,800),Rectangle(600,300)])
    def test_plan_returns_reusable_offcuts(self):
        poses, restes = planifier_panneau(3660, 2140, [(1800, 900), (1500, 600)])
        self.assertEqual(len(poses), 2)
        self.assertTrue(all(r.longueur >= 100 and r.largeur >= 100 for r in restes))

    def test_rejects_cut_larger_than_available_material(self):
        with self.assertRaisesRegex(ValueError, "ne rentre pas"):
            planifier_panneau(1000, 800, [(1200, 500)])


class OffcutReusePlanificationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("reuse-operateur", password="secret")
        self.user.user_permissions.add(Permission.objects.get(codename="plan_cut"))
        self.emplacement = Emplacement.objects.create(code="B-01-01", chariot="B", niveau=1, case=1)
        self.type_verre = TypeVerre.objects.create(designation="Verre standard")
        self.epaisseur = Epaisseur.objects.create(valeur="4.00")
        self.teinte = Teinte.objects.create(designation="Clair")
        self.client.force_login(self.user)

    def _post_data(self, **extra):
        data = {
            "longueur_panneau": 1000, "largeur_panneau": 800,
            "epaisseur": "4.00", "teinte": "Clair", "emplacement": self.emplacement.pk,
            "decoupes": "700 x 500",
        }
        data.update(extra)
        return data

    def test_preview_suggests_rotated_compatible_offcut(self):
        chute = Chute.objects.create(
            longueur=500, largeur=700, type_verre=self.type_verre,
            epaisseur=self.epaisseur, teinte=self.teinte, emplacement=self.emplacement,
        )
        response = self.client.post("/decoupes/", self._post_data(action="previsualiser"))
        self.assertContains(response, "chute existante permet")
        self.assertContains(response, f'value="{chute.pk}"')
        self.assertContains(response, chute.numero)

    def test_use_action_opens_planning_with_the_selected_offcut_prefilled(self):
        chute = Chute.objects.create(
            longueur=800, largeur=500, type_verre=self.type_verre,
            epaisseur=self.epaisseur, teinte=self.teinte, emplacement=self.emplacement,
        )

        response = self.client.get("/decoupes/", {
            "chute": chute.pk, "longueur": 700, "largeur": 500,
        })

        self.assertContains(response, f'value="{chute.pk}"')
        self.assertContains(response, 'value="800"')
        self.assertContains(response, '700 x 500')
        self.assertContains(response, "Chute sélectionnée")

    def test_closest_dimensions_win_when_two_offcuts_have_the_same_area(self):
        less_precise = Chute.objects.create(
            longueur=900, largeur=600, type_verre=self.type_verre,
            epaisseur=self.epaisseur, teinte=self.teinte, emplacement=self.emplacement,
        )
        meilleur_choix = Chute.objects.create(
            longueur=800, largeur=675, type_verre=self.type_verre,
            epaisseur=self.epaisseur, teinte=self.teinte, emplacement=self.emplacement,
        )

        resultats = compatibles(700, 500, epaisseur=self.epaisseur, teinte=self.teinte)

        self.assertEqual(resultats, [meilleur_choix, less_precise])

    def test_validation_uses_selected_offcut_without_creating_panel(self):
        chute = Chute.objects.create(
            longueur=700, largeur=500, type_verre=self.type_verre,
            epaisseur=self.epaisseur, teinte=self.teinte, emplacement=self.emplacement,
        )
        response = self.client.post("/decoupes/", self._post_data(chute_0=chute.pk, action="valider"))
        self.assertRedirects(response, "/stockage/")
        decoupe = Decoupe.objects.get()
        self.assertEqual(decoupe.chute_source, chute)
        chute.refresh_from_db()
        self.assertEqual(chute.etat, Chute.Etat.UTILISEE)

    def test_preview_displays_the_graphical_cut_plan_for_selected_offcut(self):
        chute = Chute.objects.create(
            longueur=800, largeur=500, type_verre=self.type_verre,
            epaisseur=self.epaisseur, teinte=self.teinte, emplacement=self.emplacement,
        )

        response = self.client.post("/decoupes/", self._post_data(chute_0=chute.pk, action="previsualiser"))

        self.assertContains(response, "Plan de découpe de la chute")
        self.assertContains(response, chute.numero)
        self.assertContains(response, 'viewBox="0 0 800 500"')
        self.assertContains(response, "100 × 500 mm")
        self.assertEqual(response.context["restes"], [])

    def test_can_consume_an_offcut_without_storing_its_remainders(self):
        chute = Chute.objects.create(
            longueur=800, largeur=500, type_verre=self.type_verre,
            epaisseur=self.epaisseur, teinte=self.teinte, emplacement=self.emplacement,
        )

        response = self.client.post("/decoupes/", self._post_data(
            chute_0=chute.pk, consommer_integralement_0="1", action="valider",
        ))

        self.assertRedirects(response, "/stockage/")
        chute.refresh_from_db()
        self.assertEqual(chute.etat, Chute.Etat.UTILISEE)
        self.assertFalse(Chute.objects.filter(longueur=100, largeur=500, etat=Chute.Etat.DISPONIBLE).exists())

    def test_smart_search_can_cut_directly_from_a_result(self):
        chute = Chute.objects.create(
            longueur=800, largeur=500, type_verre=self.type_verre,
            epaisseur=self.epaisseur, teinte=self.teinte, emplacement=self.emplacement,
        )
        response = self.client.post(f"/stockage/rechercher/decouper/{chute.pk}/", {
            "longueur": 700, "largeur": 500,
            "epaisseur": self.epaisseur.pk, "teinte": self.teinte.pk,
        })
        self.assertRedirects(response, "/stockage/")
        chute.refresh_from_db()
        self.assertEqual(chute.etat, Chute.Etat.UTILISEE)
        self.assertTrue(Chute.objects.filter(etat=Chute.Etat.DISPONIBLE, longueur=100, largeur=500).exists())

        stock = self.client.get("/stockage/")
        self.assertNotContains(stock, chute.numero)

    def test_smart_search_removes_fully_consumed_offcut_from_active_stock(self):
        chute = Chute.objects.create(
            longueur=700, largeur=500, type_verre=self.type_verre,
            epaisseur=self.epaisseur, teinte=self.teinte, emplacement=self.emplacement,
        )

        response = self.client.post(f"/stockage/rechercher/decouper/{chute.pk}/", {
            "longueur": 700, "largeur": 500,
            "epaisseur": self.epaisseur.pk, "teinte": self.teinte.pk,
        })

        self.assertRedirects(response, "/stockage/")
        chute.refresh_from_db()
        self.assertEqual(chute.etat, Chute.Etat.UTILISEE)
        self.assertFalse(Chute.objects.filter(pk=chute.pk, etat=Chute.Etat.DISPONIBLE).exists())
        self.assertNotContains(self.client.get("/stockage/"), chute.numero)


class PlanificationViewTests(TestCase):
    def test_planning_url_rejects_authenticated_user_without_permission(self):
        user = get_user_model().objects.create_user("reception", password="secret")
        self.client.force_login(user)
        self.assertEqual(self.client.get("/decoupes/").status_code, 403)

    def test_preview_displays_the_graphical_cut_plan(self):
        user = get_user_model().objects.create_user("operateur", password="secret")
        user.user_permissions.add(Permission.objects.get(codename="plan_cut"))
        emplacement = Emplacement.objects.create(code="A-01-01", chariot="A", niveau=1, case=1)
        self.client.force_login(user)
        response = self.client.post("/decoupes/", {
            "longueur_panneau": 1000,
            "largeur_panneau": 800,
            "epaisseur": "4.00",
            "teinte": "Clair",
            "emplacement": emplacement.pk,
            "decoupes": "600 x 500",
            "action": "previsualiser",
        })
        self.assertContains(response, "Plan de découpe du panneau")
        self.assertContains(response, "1000 × 800 mm")
