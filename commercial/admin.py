from django.contrib import admin

from .models import DemandeDevis, Devis, HistoriqueDevis, LigneDevis


class LigneDevisInline(admin.TabularInline):
    model = LigneDevis
    extra = 0
    fields = ("description", "type_verre", "epaisseur", "longueur", "largeur", "quantite", "prix_unitaire", "montant", "decoupe", "rabotage", "percage", "trempe", "autres_prestations")
    readonly_fields = ("prix_unitaire", "montant")


class HistoriqueDevisInline(admin.TabularInline):
    model = HistoriqueDevis
    extra = 0
    can_delete = False
    fields = ("ancien_statut", "nouveau_statut", "utilisateur", "date", "commentaire")
    readonly_fields = fields


@admin.register(DemandeDevis)
class DemandeDevisAdmin(admin.ModelAdmin):
    list_display = ("id", "titre", "client", "priorite", "date_souhaitee", "statut", "dimensions", "quantite", "cree_le")
    list_filter = ("statut", "priorite", "pose_souhaitee", "type_verre", "epaisseur", "cree_le")
    search_fields = ("titre", "client__nom", "description", "produits", "dimensions", "prestations", "chantier_adresse")
    autocomplete_fields = ("client", "type_verre", "epaisseur", "cree_par")
    readonly_fields = ("cree_le", "cree_par")
    date_hierarchy = "cree_le"


@admin.register(Devis)
class DevisAdmin(admin.ModelAdmin):
    list_display = ("reference", "client", "statut", "date", "validite", "total_ttc", "cree_par")
    list_filter = ("statut", "date", "validite")
    search_fields = ("reference", "client__nom", "observations")
    autocomplete_fields = ("client", "demande", "cree_par")
    readonly_fields = ("reference", "date", "sous_total", "total_ht", "total_ttc", "cree_par")
    inlines = (LigneDevisInline, HistoriqueDevisInline)
    date_hierarchy = "date"


@admin.register(LigneDevis)
class LigneDevisAdmin(admin.ModelAdmin):
    list_display = ("description", "devis", "quantite", "prix_unitaire", "montant")
    search_fields = ("description", "devis__reference", "devis__client__nom")
    list_filter = ("type_verre", "epaisseur")
    autocomplete_fields = ("devis", "type_verre", "epaisseur")
    readonly_fields = ("prix_unitaire", "montant")


@admin.register(HistoriqueDevis)
class HistoriqueDevisAdmin(admin.ModelAdmin):
    list_display = ("devis", "ancien_statut", "nouveau_statut", "utilisateur", "date")
    list_filter = ("nouveau_statut", "date")
    search_fields = ("devis__reference", "devis__client__nom", "utilisateur__username")
    autocomplete_fields = ("devis", "utilisateur")
    readonly_fields = ("devis", "ancien_statut", "nouveau_statut", "utilisateur", "date", "commentaire")
