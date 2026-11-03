from django.db import migrations, models


def preserve_legacy_inventory(apps, schema_editor):
    Inventory = apps.get_model("excel_thing", "Inventory")
    LegacyInventory = apps.get_model("excel_thing", "LegacyInventory")
    LegacyInventory.objects.using(schema_editor.connection.alias).bulk_create(
        [
            LegacyInventory(material=row.material, on_hand=row.on_hand)
            for row in Inventory.objects.using(schema_editor.connection.alias).all().iterator()
        ],
        batch_size=1000,
    )


def restore_legacy_inventory(apps, schema_editor):
    Inventory = apps.get_model("excel_thing", "Inventory")
    LegacyInventory = apps.get_model("excel_thing", "LegacyInventory")
    Inventory.objects.using(schema_editor.connection.alias).bulk_create(
        [
            Inventory(material=row.material, on_hand=row.on_hand)
            for row in LegacyInventory.objects.using(schema_editor.connection.alias).all().iterator()
        ],
        batch_size=1000,
    )


class Migration(migrations.Migration):
    dependencies = [("excel_thing", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="LegacyInventory",
            fields=[
                (
                    "material",
                    models.CharField(max_length=50, primary_key=True, serialize=False),
                ),
                (
                    "on_hand",
                    models.DecimalField(
                        decimal_places=2, default=0.0, max_digits=12
                    ),
                ),
            ],
        ),
        migrations.RunPython(
            preserve_legacy_inventory,
            reverse_code=restore_legacy_inventory,
        ),
        migrations.DeleteModel(name="Inventory"),
        migrations.CreateModel(
            name="Inventory",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "item_class",
                    models.CharField(max_length=50, verbose_name="Class"),
                ),
                (
                    "item_number",
                    models.CharField(max_length=50, verbose_name="Item Number"),
                ),
                (
                    "revision",
                    models.CharField(blank=True, max_length=50, verbose_name="Rev"),
                ),
                ("description", models.CharField(blank=True, max_length=255)),
                ("standard_cost", models.DecimalField(decimal_places=16, max_digits=24)),
                ("on_hand", models.DecimalField(decimal_places=2, max_digits=14)),
                ("non_conform", models.DecimalField(decimal_places=2, max_digits=14)),
            ],
        ),
    ]
