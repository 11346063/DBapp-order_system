from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("web_app", "0018_cart_cartitem_cartitemoption_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="ready_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="order",
            name="ready_notified_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="order",
            name="status",
            field=models.IntegerField(
                choices=[
                    (0, "等待中"),
                    (1, "已完成"),
                    (2, "已取消"),
                    (3, "可取餐"),
                ],
                default=0,
            ),
        ),
    ]
