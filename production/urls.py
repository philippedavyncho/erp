from django.urls import path
from . import views
app_name="production"
urlpatterns=[path("",views.liste,name="liste"),path("creer/<int:commande_pk>/",views.creer,name="creer"),path("<int:pk>/",views.detail,name="detail"),path("etape/<int:pk>/<str:statut>/",views.etape,name="etape")]
