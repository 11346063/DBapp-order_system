from django.db import migrations


def _seed_store_settings(apps, schema_editor):
    StoreSettings = apps.get_model("web_app", "StoreSettings")
    StoreSettings.objects.get_or_create(
        pk=1,
        defaults={
            "extra_ingredient_cost": 10,
            "option_name_spicy": "辣度",
            "option_name_garlic": "加蒜",
            "option_name_basil": "九層塔",
            "option_name_cut": "切",
        },
    )


class Migration(migrations.Migration):
    dependencies = [
        ("web_app", "0027_custom_option_fields"),
    ]

    operations = [
        migrations.RunPython(_seed_store_settings, migrations.RunPython.noop),
    ]
