from django.db import migrations


SEED_OPTIONS = [
    {"name": "辣度", "price": 0},
    {"name": "加蒜", "price": 10},
    {"name": "九層塔", "price": 10},
    {"name": "切", "price": 0},
]

CUT_MENU_NAMES = ["炸雞排", "碳烤香雞排", "烤雞排"]


def seed_options_and_optgroup(apps, schema_editor):
    Options = apps.get_model("web_app", "Options")
    OptGroup = apps.get_model("web_app", "OptGroup")
    Menu = apps.get_model("web_app", "Menu")

    for opt_data in SEED_OPTIONS:
        Options.objects.get_or_create(name=opt_data["name"], defaults={"price": opt_data["price"]})

    cut_opt = Options.objects.filter(name="切").first()
    if cut_opt:
        for menu_name in CUT_MENU_NAMES:
            menu = Menu.objects.filter(name=menu_name).first()
            if menu:
                OptGroup.objects.get_or_create(menu=menu, opt=cut_opt)


def remove_seeded_data(apps, schema_editor):
    Options = apps.get_model("web_app", "Options")
    OptGroup = apps.get_model("web_app", "OptGroup")

    cut_opt = Options.objects.filter(name="切").first()
    if cut_opt:
        OptGroup.objects.filter(opt=cut_opt).delete()

    Options.objects.filter(name__in=[o["name"] for o in SEED_OPTIONS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("web_app", "0011_orderitemoptions_refactor_orderitem_notes_remove"),
    ]

    operations = [
        migrations.RunPython(seed_options_and_optgroup, remove_seeded_data),
    ]
