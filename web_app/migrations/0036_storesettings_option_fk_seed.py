from django.db import migrations

from web_app.constants import OPTION_BASIL, OPTION_CUT, OPTION_GARLIC, OPTION_SPICY


def _seed_fk(apps, schema_editor):
    StoreSettings = apps.get_model("web_app", "StoreSettings")
    Options = apps.get_model("web_app", "Options")

    obj = StoreSettings.objects.filter(pk=1).first()
    if obj is None:
        return

    def _get(name):
        return Options.objects.filter(name=name).first()

    obj.spicy_option = _get(OPTION_SPICY)
    obj.garlic_option = _get(OPTION_GARLIC)
    obj.basil_option = _get(OPTION_BASIL)
    obj.cut_option = _get(OPTION_CUT)
    obj.save(
        update_fields=["spicy_option", "garlic_option", "basil_option", "cut_option"]
    )


class Migration(migrations.Migration):
    dependencies = [
        ("web_app", "0035_storesettings_option_fk"),
    ]

    operations = [
        migrations.RunPython(_seed_fk, migrations.RunPython.noop),
    ]
