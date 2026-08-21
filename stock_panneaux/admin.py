from django.contrib import admin

from .models import MouvementStockGrandPanneau, PlanificationStock, StockGrandPanneau

admin.site.register(StockGrandPanneau)
admin.site.register(MouvementStockGrandPanneau)
admin.site.register(PlanificationStock)
