from django.urls import path
from . import views

app_name = "mouvements"
urlpatterns = [path("", views.liste, name="liste")]
