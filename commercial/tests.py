from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from clients.models import Client
from chutes.models import Chute
from emplacements.models import Emplacement
from commandes.models import Commande
from stock_panneaux.models import MouvementStockGrandPanneau, StockGrandPanneau
from types_verres.models import Epaisseur, Teinte, TypeVerre
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

    def test_accepting_quote_keeps_material_available_until_cutting_is_planned(self):
        self.user.user_permissions.add(Permission.objects.get(codename="send_devis"), Permission.objects.get(codename="accept_devis"))
        verre = TypeVerre.objects.create(designation="Clair", prix_m2=Decimal("1000"))
        epaisseur = Epaisseur.objects.create(valeur="4.00")
        teinte = Teinte.objects.create(designation="Neutre")
        panneau = StockGrandPanneau.objects.create(reference="GP-DEV", materiau=verre, epaisseur=epaisseur, teinte=teinte, longueur=1000, largeur=800, quantite_en_stock=2)
        emplacement = Emplacement.objects.create(code="T-01", chariot="T", niveau=1, case=1)
        chute = Chute.objects.create(longueur=700, largeur=500, type_verre=verre, epaisseur=epaisseur, teinte=teinte, emplacement=emplacement)
        devis = Devis.objects.create(client=self.client_obj)
        LigneDevis.objects.create(devis=devis, description="Panneau", type_verre=verre, epaisseur=epaisseur, longueur=900, largeur=600, quantite=1, panneau_stock=panneau)
        LigneDevis.objects.create(devis=devis, description="Chute", type_verre=verre, epaisseur=epaisseur, longueur=700, largeur=500, quantite=1, chute_stock=chute)

        changer_statut_devis(devis, Devis.Statut.ENVOYE, self.user)
        panneau.refresh_from_db(); chute.refresh_from_db()
        self.assertEqual(panneau.quantite_en_stock, 2)
        self.assertEqual(chute.etat, Chute.Etat.DISPONIBLE)
        changer_statut_devis(devis, Devis.Statut.ACCEPTE, self.user)
        panneau.refresh_from_db(); chute.refresh_from_db()
        self.assertEqual(panneau.quantite_en_stock, 2)
        self.assertEqual(chute.etat, Chute.Etat.DISPONIBLE)
        self.assertFalse(MouvementStockGrandPanneau.objects.exists())
        self.assertTrue(Commande.objects.filter(devis=devis, statut=Commande.Statut.NOUVELLE).exists())

    def test_quote_pdf_is_generated_as_a_complete_document(self):
        self.user.user_permissions.add(Permission.objects.get(codename="view_devis"))
        devis = Devis.objects.create(client=self.client_obj)
        LigneDevis.objects.create(devis=devis, description="Vitre sur mesure", longueur=800, largeur=600, quantite=1, prix_unitaire=Decimal("12000"))
        devis.recalculer_totaux()
        self.client.force_login(self.user)
        response = self.client.get(f"/commercial/devis/{devis.pk}/pdf/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertGreater(len(response.content), 1000)

    def test_line_includes_fabrication_or_installation_flat_fee(self):
        verre = TypeVerre.objects.create(designation="Verre 4 mm", prix_m2=Decimal("10000"))
        devis = Devis.objects.create(client=self.client_obj)
        ligne = LigneDevis.objects.create(devis=devis, description="Vitre percée", type_verre=verre, longueur=1000, largeur=500, quantite=1, prix_prestations=Decimal("3500"))
        self.assertEqual(ligne.montant, Decimal("8500"))

    def test_quote_request_qualifies_the_site_and_prefills_the_quote(self):
        self.user.user_permissions.add(
            Permission.objects.get(codename="add_demandedevis"),
            Permission.objects.get(codename="add_devis"),
        )
        self.client.force_login(self.user)
        response = self.client.post("/commercial/demandes/nouvelle/", {
            "client": self.client_obj.pk,
            "titre": "Vitrine boutique",
            "description": "Remplacement d'une vitre fissurée.",
            "quantite": 1,
            "chantier_adresse": "12 rue des Fleurs",
            "contact_chantier": "Mme Diallo",
            "telephone_chantier": "0102030405",
            "date_souhaitee": "2026-10-15",
            "priorite": "HAUTE",
            "pose_souhaitee": "on",
            "prise_mesures_souhaitee": "on",
        })
        self.assertEqual(response.status_code, 302)

        demande = self.client_obj.demandes_devis.get()
        response = self.client.get(f"/commercial/devis/nouveau/?demande={demande.pk}")
        self.assertEqual(response.context["form"].initial["client"], self.client_obj.pk)
        self.assertEqual(response.context["form"].initial["chantier_adresse"], "12 rue des Fleurs")
        self.assertTrue(response.context["form"].initial["pose_incluse"])
