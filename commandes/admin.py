from django.contrib import admin

from .models import Commande, HistoriqueCommande, LigneCommande


class LigneCommandeInline(admin.TabularInline):
    model = LigneCommande
    extra = 0
    readonly_fields = ("description", "type_verre", "epaisseur", "longueur", "largeur", "quantite", "decoupe", "rabotage", "percage", "trempe", "autres_prestations")
    can_delete = False


class HistoriqueCommandeInline(admin.TabularInline):
    model = HistoriqueCommande
    extra = 0
    can_delete = False
    readonly_fields = ("ancien_statut", "nouveau_statut", "date", "utilisateur", "commentaire")


@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = ("reference", "client", "statut", "priorite", "date", "date_prevue", "valide_par")
    list_filter = ("statut", "priorite", "date", "date_prevue")
    search_fields = ("reference", "client__nom", "devis__reference")
    autocomplete_fields = ("client", "devis", "cree_par", "valide_par")
    readonly_fields = ("reference", "date", "cree_par", "valide_par")
    inlines = (LigneCommandeInline, HistoriqueCommandeInline)
    date_hierarchy = "date"


@admin.register(LigneCommande)
class LigneCommandeAdmin(admin.ModelAdmin):
    list_display = ("description", "commande", "quantite", "longueur", "largeur")
    search_fields = ("description", "commande__reference", "commande__client__nom")
    autocomplete_fields = ("commande", "type_verre", "epaisseur")


@admin.register(HistoriqueCommande)
class HistoriqueCommandeAdmin(admin.ModelAdmin):
    list_display = ("commande", "ancien_statut", "nouveau_statut", "utilisateur", "date")
    list_filter = ("nouveau_statut", "date")
    search_fields = ("commande__reference", "utilisateur__username")
    autocomplete_fields = ("commande", "utilisateur")
    readonly_fields = ("commande", "ancien_statut", "nouveau_statut", "utilisateur", "date", "commentaire")
