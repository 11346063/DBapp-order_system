import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from web_app.models import Order

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Order, dispatch_uid="web_app.order_audit_log")
def log_order_saved(sender, instance, created, **kwargs):
    if created:
        logger.info(
            "Order created",
            extra={
                "order_id": instance.pk,
                "order_status": instance.status,
                "order_total": instance.price_total,
            },
        )
