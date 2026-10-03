from django.conf import settings
from django.db import models

from carts.models import Cart
from store.models import Product


class Order(models.Model):
    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PAID = 'paid', 'Paid'
        FAILED = 'failed', 'Failed'
        CANCELLED = 'cancelled', 'Cancelled'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
    )
    cart = models.ForeignKey(
        Cart,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
    )
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )
    total_amount = models.PositiveIntegerField()
    stripe_checkout_session_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
    )
    stripe_payment_intent_id = models.CharField(
        max_length=255,
        blank=True,
    )
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Order #{self.pk} ({self.get_status_display()})'


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
    )
    product_name = models.CharField(max_length=200)
    unit_price = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField()

    @property
    def subtotal(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f'{self.product_name} × {self.quantity}'
