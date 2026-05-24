from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("web_app", "0021_rename_timestamp_fields"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="OrderItemOptions",
            new_name="OrderItemOption",
        ),
        migrations.RemoveConstraint(
            model_name="orderitemoption",
            name="orderitemoptions_exactly_one_fk",
        ),
        migrations.AddConstraint(
            model_name="orderitemoption",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(order__isnull=False, order_item__isnull=True)
                    | models.Q(order__isnull=True, order_item__isnull=False)
                ),
                name="orderitemoption_exactly_one_fk",
            ),
        ),
    ]
