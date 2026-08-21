from django.contrib import admin

from .models import Epaisseur, Teinte, TypeVerre


@admin.register(TypeVerre)
class TypeVerreAdmin(admin.ModelAdmin):
    list_display = ("designation", "prix_m2")
    search_fields = ("designation",)


@admin.register(Epaisseur)
class EpaisseurAdmin(admin.ModelAdmin):
    search_fields = ("valeur",)


@admin.register(Teinte)
class TeinteAdmin(admin.ModelAdmin):
    search_fields = ("designation",)
