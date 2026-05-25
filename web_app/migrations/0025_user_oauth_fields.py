from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("web_app", "0024_order_acceptance_flow"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="auth_provider",
            field=models.CharField(default="phone", max_length=10),
        ),
        migrations.AddField(
            model_name="user",
            name="google_sub",
            field=models.CharField(blank=True, max_length=128, null=True, unique=True),
        ),
    ]
