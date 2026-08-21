from django.urls import path
from . import views
app_name="chutes"
urlpatterns=[
    path("", views.liste, name="liste"),
    path("<int:pk>/", views.detail, name="detail"),
    path("<int:pk>/deplacer/", views.deplacer_chute, name="deplacer"),
    path("<int:pk>/corriger/", views.corriger_chute, name="corriger"),
    path("<int:pk>/reserver/", views.reserver_chute, name="reserver"),
    path("<int:pk>/annuler-reservation/", views.annuler_reservation_chute, name="annuler_reservation"),
    path("<int:pk>/utiliser/", views.utiliser_chute, name="utiliser"),
    path("<int:pk>/rebut/", views.rebut_chute, name="rebut"),
    path("entrees/", views.entrees, name="entrees"),
    path("sorties/", views.sorties, name="sorties"),
    path("rechercher/", views.rechercher, name="rechercher"),
    path("rechercher/decouper/<int:chute_id>/", views.utiliser_depuis_recherche, name="utiliser_recherche"),
]
