from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase

from emplacements.models import Emplacement
from types_verres.models import Epaisseur, Teinte, TypeVerre
from .models import Chute, MouvementChute
from .services import annuler_reservation, corriger, deplacer, mettre_au_rebut, reserver, utiliser


class ChuteTraceabilityTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("magasinier", password="secret")
        self.location = Emplacement.objects.create(code="A-01", chariot="A", niveau=1, case=1)
        self.new_location = Emplacement.objects.create(code="B-01", chariot="B", niveau=1, case=1)
        self.glass = TypeVerre.objects.create(designation="Clair")
        self.thickness = Epaisseur.objects.create(valeur="4.00")
        self.tint = Teinte.objects.create(designation="Neutre")

    def chute(self):
        return Chute.objects.create(longueur=1200, largeur=800, type_verre=self.glass, epaisseur=self.thickness, teinte=self.tint, emplacement=self.location)

    def test_creation_and_move_are_traced(self):
        chute = self.chute()
        self.assertEqual(chute.historique.count(), 1)
        deplacer(chute.pk, self.new_location, self.user, "Inventaire")
        chute.refresh_from_db()
        movement = chute.historique.first()
        self.assertEqual(chute.emplacement, self.new_location)
        self.assertEqual(movement.action, MouvementChute.Action.DEPLACEMENT)
        self.assertEqual(movement.ancien_emplacement, self.location)
        self.assertEqual(movement.utilisateur, self.user)

    def test_correction_preserves_previous_dimensions(self):
        chute = self.chute()
        corriger(chute.pk, {"longueur": 1150, "largeur": 800, "type_verre": self.glass, "epaisseur": self.thickness, "teinte": self.tint, "emplacement": self.location}, self.user, "Erreur de mesure")
        movement = chute.historique.first()
        self.assertIn("1200 × 800", movement.anciennes_dimensions)
        self.assertIn("1150 × 800", movement.nouvelles_dimensions)

    def test_reservation_cannot_be_duplicated_and_can_be_cancelled(self):
        chute = self.chute()
        reserver(chute.pk, "CMD-42", self.user)
        with self.assertRaisesRegex(ValueError, "disponible"):
            reserver(chute.pk, "CMD-43", self.user)
        annuler_reservation(chute.pk, self.user)
        chute.refresh_from_db()
        self.assertEqual(chute.etat, Chute.Etat.DISPONIBLE)
        self.assertEqual(chute.historique.first().action, MouvementChute.Action.ANNULATION_RESERVATION)

    def test_rebut_requires_a_reason_and_blocks_use_or_reservation(self):
        chute = self.chute()
        with self.assertRaises(ValueError):
            mettre_au_rebut(chute.pk, "", self.user)
        mettre_au_rebut(chute.pk, MouvementChute.MotifRebut.CASSE, self.user)
        chute.refresh_from_db()
        self.assertEqual(chute.etat, Chute.Etat.REBUT)
        with self.assertRaises(ValueError):
            utiliser(chute.pk, self.user)
        with self.assertRaises(ValueError):
            reserver(chute.pk, "CMD-44", self.user)

    def test_action_url_requires_specific_permission(self):
        chute = self.chute()
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(f"/stockage/{chute.pk}/deplacer/").status_code, 403)
        self.user.user_permissions.add(Permission.objects.get(codename="move_chute"))
        self.assertEqual(self.client.get(f"/stockage/{chute.pk}/deplacer/").status_code, 200)
