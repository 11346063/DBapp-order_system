from django.db import models


class CartItem(models.Model):
    cart = models.ForeignKey("Cart", on_delete=models.CASCADE, related_name="items")
    menu = models.ForeignKey("Menu", on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    base_price = models.IntegerField()
    options_price = models.IntegerField(default=0)
    unit_price = models.IntegerField()
    subtotal = models.IntegerField()
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "id"]
        indexes = [
            # 購物車頁常以 (cart, menu) 查詢同品項，加速重複品項偵測
            models.Index(fields=["cart", "menu"], name="cartitem_cart_menu_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name="cartitem_quantity_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(base_price__gte=0),
                name="cartitem_base_price_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(options_price__gte=0),
                name="cartitem_options_price_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(unit_price__gte=0),
                name="cartitem_unit_price_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(subtotal__gte=0),
                name="cartitem_subtotal_non_negative",
            ),
        ]


class CartItemOption(models.Model):
    cart_item = models.ForeignKey(
        "CartItem",
        on_delete=models.CASCADE,
        related_name="options",
    )
    opt = models.ForeignKey("Options", on_delete=models.PROTECT)
    name = models.CharField(max_length=50)
    price = models.IntegerField(default=0)
    level = models.IntegerField(default=1)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(price__gte=0),
                name="cartitemoption_price_non_negative",
            )
        ]
