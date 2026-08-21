from django.urls import path
from . import views
app_name="commandes"
urlpatterns=[path("",views.liste,name="liste"),path("<int:pk>/",views.detail,name="detail"),path("<int:pk>/valider/",views.valider,name="valider")]
