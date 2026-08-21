from django.urls import path
from . import views
app_name="impression"
urlpatterns=[path("chute/<int:pk>/",views.etiquette,name="etiquette")]
