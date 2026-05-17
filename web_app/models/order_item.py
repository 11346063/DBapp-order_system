from django.db import models


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class OrderItem(models.Model):
    order = models.ForeignKey("Order", on_delete=models.CASCADE)
    menu = models.ForeignKey("Menu", on_delete=models.PROTECT)
    amount = models.IntegerField()
    total_price = models.IntegerField()
    is_deleted = models.BooleanField(default=False)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.save(update_fields=["is_deleted"])
