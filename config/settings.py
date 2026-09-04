import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = "change-me-before-production"
DEBUG = True
ALLOWED_HOSTS: list[str] = []
INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "accounts.apps.AccountsConfig", "types_verres", "emplacements", "panneaux.apps.PanneauxConfig", "chutes.apps.ChutesConfig", "decoupes", "stock_panneaux.apps.StockPanneauxConfig",
    "mouvements", "dashboard", "impression", "clients.apps.ClientsConfig", "commercial.apps.CommercialConfig", "commandes.apps.CommandesConfig", "production.apps.ProductionConfig",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware", "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware", "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware", "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [BASE_DIR / "templates"], "APP_DIRS": True,
 "OPTIONS": {"context_processors": ["django.template.context_processors.request", "django.contrib.auth.context_processors.auth", "django.contrib.messages.context_processors.messages"]}}]
WSGI_APPLICATION = "config.wsgi.application"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": Path(os.environ.get("ERP_DATA_DIR", BASE_DIR)) / "db.sqlite3"}}
AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE, TIME_ZONE, USE_I18N, USE_TZ = "fr-fr", "Europe/Paris", True, True
STATIC_URL, STATICFILES_DIRS = "static/", [BASE_DIR / "static"]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
# À renseigner avant mise en production : ces coordonnées apparaissent sur les devis.
ENTREPRISE_NOM = os.environ.get("ERP_ENTREPRISE_NOM", "VerreStock")
ENTREPRISE_ACTIVITE = os.environ.get("ERP_ENTREPRISE_ACTIVITE", "Vitrerie · Découpe · Façonnage")
ENTREPRISE_ADRESSE = os.environ.get("ERP_ENTREPRISE_ADRESSE", "")
ENTREPRISE_TELEPHONE = os.environ.get("ERP_ENTREPRISE_TELEPHONE", "")
ENTREPRISE_EMAIL = os.environ.get("ERP_ENTREPRISE_EMAIL", "")
ENTREPRISE_IDENTIFIANT = os.environ.get("ERP_ENTREPRISE_IDENTIFIANT", "")
LOGIN_URL = "login"
LOGIN_REDIRECT_URL, LOGOUT_REDIRECT_URL = "dashboard:index", "login"
