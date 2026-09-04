from django.urls import path
from . import views
app_name="commandes"
urlpatterns=[path("",views.liste,name="liste"),path("<int:pk>/",views.detail,name="detail"),path("<int:pk>/valider/",views.valider,name="valider"),path("<int:pk>/statut/<str:statut>/",views.statut,name="statut"),path("<int:pk>/bon-livraison/",views.bon_livraison,name="bon_livraison")]
