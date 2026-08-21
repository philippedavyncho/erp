from django.contrib import admin

from .models import EtapeProduction, FicheProduction, PieceProduction


class PieceProductionInline(admin.TabularInline):
    model = PieceProduction
    extra = 0
    readonly_fields = ("reference", "ligne_commande", "quantite", "statut")
    can_delete = False


@admin.register(FicheProduction)
class FicheProductionAdmin(admin.ModelAdmin):
    list_display = ("reference", "commande", "statut", "priorite", "cree_le", "cree_par")
    list_filter = ("statut", "priorite", "cree_le")
    search_fields = ("reference", "commande__reference", "commande__client__nom")
    autocomplete_fields = ("commande", "cree_par")
    readonly_fields = ("reference", "cree_le", "cree_par")
    inlines = (PieceProductionInline,)
    date_hierarchy = "cree_le"


class EtapeProductionInline(admin.TabularInline):
    model = EtapeProduction
    extra = 0
    fields = ("type", "statut", "operateur", "debut", "fin", "commentaire", "probleme")


@admin.register(PieceProduction)
class PieceProductionAdmin(admin.ModelAdmin):
    list_display = ("reference", "fiche", "ligne_commande", "quantite", "statut")
    list_filter = ("statut",)
    search_fields = ("reference", "fiche__reference", "ligne_commande__description")
    autocomplete_fields = ("fiche", "ligne_commande")
    inlines = (EtapeProductionInline,)


@admin.register(EtapeProduction)
class EtapeProductionAdmin(admin.ModelAdmin):
    list_display = ("piece", "type", "statut", "operateur", "debut", "fin")
    list_filter = ("type", "statut", "debut", "fin")
    search_fields = ("piece__reference", "piece__fiche__reference", "operateur__username", "probleme")
    autocomplete_fields = ("piece", "operateur")
