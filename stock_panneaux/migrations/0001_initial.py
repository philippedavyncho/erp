from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL), ("panneaux", "0003_remove_panneau_prix"), ("types_verres", "0002_delete_finition")]
    operations = [
        migrations.CreateModel(name="StockGrandPanneau", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("reference", models.CharField(max_length=80, unique=True)),
            ("longueur", models.PositiveIntegerField(help_text="mm")), ("largeur", models.PositiveIntegerField(help_text="mm")), ("quantite_en_stock", models.PositiveIntegerField(default=0)), ("quantite_minimum", models.PositiveIntegerField(default=0)),
            ("date_creation", models.DateTimeField(auto_now_add=True)), ("date_modification", models.DateTimeField(auto_now=True)),
            ("epaisseur", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="types_verres.epaisseur")), ("materiau", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="types_verres.typeverre", verbose_name="Matériau")), ("teinte", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="types_verres.teinte", verbose_name="Couleur")),
        ], options={"ordering": ["reference"], "verbose_name": "stock de grand panneau", "verbose_name_plural": "stocks de grands panneaux"}),
        migrations.CreateModel(name="MouvementStockGrandPanneau", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("type", models.CharField(choices=[("ENTREE", "Entrée"), ("SORTIE", "Sortie")], max_length=10)), ("quantite", models.PositiveIntegerField()), ("origine", models.CharField(max_length=120)), ("date", models.DateTimeField(auto_now_add=True)),
            ("panneau", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="mouvements", to="stock_panneaux.stockgrandpanneau")), ("utilisateur", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
        ], options={"ordering": ["-date"]}),
        migrations.CreateModel(name="PlanificationStock", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("quantite", models.PositiveIntegerField(default=1)), ("statut", models.CharField(choices=[("VALIDEE", "Validée"), ("ANNULEE", "Annulée")], default="VALIDEE", max_length=10)), ("cree_le", models.DateTimeField(auto_now_add=True)), ("annule_le", models.DateTimeField(blank=True, null=True)),
            ("panneau_stock", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="planifications", to="stock_panneaux.stockgrandpanneau")), ("panneau_utilise", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="consommation_stock", to="panneaux.panneau")), ("utilisateur", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
        ]),
    ]
