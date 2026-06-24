from django.db import migrations


class Migration(migrations.Migration):
    """移除 Cart / CartItem / CartItemOption — 購物車改由前端 localStorage 管理。"""

    dependencies = [
        ("web_app", "0032_printjob"),
    ]

    operations = [
        migrations.DeleteModel(name="CartItemOption"),
        migrations.DeleteModel(name="CartItem"),
        migrations.DeleteModel(name="Cart"),
    ]
