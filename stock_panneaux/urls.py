from django.urls import path

from . import views

app_name = "stock_panneaux"
urlpatterns = [
    path("", views.liste, name="liste"),
    path("entrees/", views.entrees, name="entrees"),
    path("sorties/", views.sorties, name="sorties"),
    path("nouveau/", views.creer, name="creer"),
    path("<int:pk>/reception/", views.receptionner, name="receptionner"),
    path("<int:pk>/modifier/", views.modifier, name="modifier"),
    path("<int:pk>/supprimer/", views.supprimer, name="supprimer"),
    path("historique/", views.historique, name="historique"),
    path("planifications/<int:pk>/annuler/", views.annuler, name="annuler"),
]
