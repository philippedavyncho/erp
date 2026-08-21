from django.contrib import admin
from django.urls import include, path
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("dashboard.urls")),
    path("tableau-de-bord/", RedirectView.as_view(url="/", permanent=False)),
    path("decoupes/", include("decoupes.urls")),
    path("grands-panneaux/", include("stock_panneaux.urls")),
    path("mouvements/", include("mouvements.urls")),
    path("stockage/", include("chutes.urls")),
    path("clients/", include("clients.urls")),
    path("commercial/", include("commercial.urls")),
    path("commandes/", include("commandes.urls")),
    path("production/", include("production.urls")),
    path("connexion/", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("deconnexion/", auth_views.LogoutView.as_view(), name="logout"),
]
