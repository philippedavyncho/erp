from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from clients.models import Client
from commandes.models import Commande, LigneCommande
from .models import EtapeProduction, FicheProduction
from .services import changer_etape, creer_fiche
class ProductionTests(TestCase):
    def test_validated_order_creates_production_steps(self):
        user=get_user_model().objects.create_user("prod"); order=Commande.objects.create(client=Client.objects.create(nom="Client"),statut=Commande.Statut.VALIDEE); LigneCommande.objects.create(commande=order,description="Pièce",longueur=1000,largeur=500,quantite=1,rabotage=True)
        fiche=creer_fiche(order,user); self.assertEqual(fiche.pieces.count(),1); self.assertEqual(fiche.pieces.first().etapes.count(),3)

    def test_steps_drive_production_and_order_statuses(self):
        user=get_user_model().objects.create_user("atelier")
        order=Commande.objects.create(client=Client.objects.create(nom="Client"),statut=Commande.Statut.VALIDEE)
        LigneCommande.objects.create(commande=order,description="Pièce",longueur=1000,largeur=500,quantite=1,rabotage=True)
        fiche=creer_fiche(order,user)
        etapes=list(fiche.pieces.first().etapes.order_by("pk"))
        changer_etape(etapes[0], EtapeProduction.Statut.EN_COURS, user)
        fiche.refresh_from_db(); order.refresh_from_db()
        self.assertEqual(fiche.statut, FicheProduction.Statut.EN_COURS)
        self.assertEqual(order.statut, Commande.Statut.EN_PRODUCTION)
        changer_etape(etapes[0], EtapeProduction.Statut.TERMINE, user)
        changer_etape(etapes[1], EtapeProduction.Statut.EN_COURS, user)
        changer_etape(etapes[1], EtapeProduction.Statut.TERMINE, user)
        changer_etape(etapes[2], EtapeProduction.Statut.EN_COURS, user)
        changer_etape(etapes[2], EtapeProduction.Statut.TERMINE, user)
        fiche.refresh_from_db(); order.refresh_from_db()
        self.assertEqual(fiche.statut, FicheProduction.Statut.TERMINEE)
        self.assertEqual(order.statut, Commande.Statut.TERMINEE)

    def test_creating_a_production_sheet_is_audited_and_invalid_status_is_rejected(self):
        user = get_user_model().objects.create_user("responsable_atelier")
        order = Commande.objects.create(client=Client.objects.create(nom="Client"), statut=Commande.Statut.VALIDEE)
        line = LigneCommande.objects.create(commande=order, description="Piece", longueur=1000, largeur=500, quantite=1)

        fiche = creer_fiche(order, user)
        order.refresh_from_db()
        self.assertEqual(order.statut, Commande.Statut.EN_PREPARATION)
        self.assertEqual(order.historique.get().nouveau_statut, Commande.Statut.EN_PREPARATION)

        etape = fiche.pieces.get(ligne_commande=line).etapes.get(type=EtapeProduction.Type.DECOUPE)
        with self.assertRaisesMessage(ValueError, "Statut d'op\u00e9ration invalide"):
            changer_etape(etape, "INVALIDE", user)

    def test_piece_qr_label_opens_the_piece_workflow(self):
        user = get_user_model().objects.create_user("operateur_qr")
        user.user_permissions.add(Permission.objects.get(codename="view_ficheproduction"))
        order = Commande.objects.create(client=Client.objects.create(nom="Client"), statut=Commande.Statut.VALIDEE)
        line = LigneCommande.objects.create(commande=order, description="Vitrine", longueur=1000, largeur=500, quantite=1)
        fiche = creer_fiche(order, user)
        piece = fiche.pieces.get(ligne_commande=line)
        self.client.force_login(user)

        workflow = self.client.get(f"/production/piece/{piece.pk}/")
        label = self.client.get(f"/impression/piece/{piece.pk}/")

        self.assertContains(workflow, piece.reference)
        self.assertEqual(label.status_code, 200)
        self.assertEqual(label["Content-Type"], "application/pdf")
        self.assertGreater(len(label.content), 1000)
