from django.contrib import admin
from .models import Chute, MouvementChute


@admin.register(Chute)
class ChuteAdmin(admin.ModelAdmin):
    list_display = ("numero", "etat", "emplacement", "longueur", "largeur", "modifie_le")
    list_filter = ("etat", "type_verre", "epaisseur", "teinte")
    search_fields = ("numero", "emplacement__code")


@admin.register(MouvementChute)
class MouvementChuteAdmin(admin.ModelAdmin):
    list_display = ("date", "chute", "action", "utilisateur", "motif")
    list_filter = ("action", "motif")
    readonly_fields = tuple(field.name for field in MouvementChute._meta.fields)
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
