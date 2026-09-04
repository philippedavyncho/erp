from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("production", "0001_initial"),
        ("decoupes", "0002_alter_decoupe_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="decoupe",
            name="piece_production",
            field=models.ForeignKey(
                blank=True,
                help_text="Pièce de production réalisée par cette découpe.",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="decoupes",
                to="production.pieceproduction",
            ),
        ),
    ]
