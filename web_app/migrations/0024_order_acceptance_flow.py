from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def migrate_status_values(apps, schema_editor):
    """
    Old → New status mapping:
      PENDING(0)    → ACCEPTED(1)   舊等待中視為已接單
      COMPLETED(1)  → COMPLETED(3)
      CANCELLED(2)  → CANCELLED(4)
      READY(3)      → READY(2)
    """
    Order = apps.get_model("web_app", "Order")
    db = schema_editor.connection.alias

    # Use temp value 20 to avoid collision when remapping 3→2
    Order.objects.using(db).filter(status=3).update(status=20)
    Order.objects.using(db).filter(status=2).update(status=4)
    Order.objects.using(db).filter(status=1).update(status=3)
    Order.objects.using(db).filter(status=0).update(status=1)
    Order.objects.using(db).filter(status=20).update(status=2)


class Migration(migrations.Migration):
    dependencies = [
        ("web_app", "0023_add_composite_indexes"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="accepted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="order",
            name="accepted_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="accepted_orders",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="estimated_wait_minutes",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="order",
            name="cancel_reason",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
        migrations.AddField(
            model_name="order",
            name="pickup_code",
            field=models.CharField(blank=True, default="", max_length=12),
        ),
        migrations.RunPython(migrate_status_values, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="order",
            name="status",
            field=models.IntegerField(
                choices=[
                    (0, "等待接單"),
                    (1, "備餐中"),
                    (2, "可取餐"),
                    (3, "已完成"),
                    (4, "已取消"),
                ],
                default=0,
            ),
        ),
    ]
