from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("web_app", "0008_remove_order_sno"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="customer_phone",
            field=models.CharField(blank=True, default="", max_length=20),
        ),
    ]
