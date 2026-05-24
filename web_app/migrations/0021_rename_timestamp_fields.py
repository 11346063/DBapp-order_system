from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("web_app", "0020_order_create_time_default"),
    ]

    operations = [
        migrations.RenameField(
            model_name="order",
            old_name="create_time",
            new_name="created_at",
        ),
        migrations.RenameField(
            model_name="user",
            old_name="create_time",
            new_name="created_at",
        ),
        migrations.RenameField(
            model_name="user",
            old_name="update_time",
            new_name="updated_at",
        ),
    ]
