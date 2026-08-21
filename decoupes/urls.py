from django.urls import path
from . import views
app_name="decoupes"
urlpatterns=[path("", views.planifier, name="planifier")]
