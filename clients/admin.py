from django.contrib import admin

from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("reference", "nom", "contact", "telephone", "email", "ville", "cree_le")
    search_fields = ("reference", "nom", "contact", "telephone", "email", "ville")
    list_filter = ("ville", "cree_le")
    readonly_fields = ("reference", "cree_le", "cree_par")
    ordering = ("nom",)
