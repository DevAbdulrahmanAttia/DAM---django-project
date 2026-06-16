from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class OrderStatus(models.TextChoices):
    PENDING = 'pending', _('Pending')
    CONFIRMED = 'confirmed', _('Confirmed')
    PROCESSING = 'processing', _('Processing')
    SHIPPED = 'shipped', _('Shipped')
    DELIVERED = 'delivered', _('Delivered')
    CANCELLED = 'cancelled', _('Cancelled')


class Order(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='orders',
        verbose_name=_('user'),
        null=True,
        blank=True,
    )
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
        db_index=True,
    )
    subtotal = models.DecimalField(
        _('subtotal'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    shipping_cost = models.DecimalField(
        _('shipping cost'),
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    total = models.DecimalField(
        _('total'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('order')
        verbose_name_plural = _('orders')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f'Order #{self.pk} - {self.get_status_display()}'


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('order'),
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.SET_NULL,
        related_name='order_items',
        verbose_name=_('product'),
        null=True,
        blank=True,
    )
    seller = models.ForeignKey(
        'vendors.Seller',
        on_delete=models.SET_NULL,
        related_name='order_items',
        verbose_name=_('seller'),
        null=True,
        blank=True,
    )
    quantity = models.PositiveIntegerField(
        _('quantity'),
        validators=[MinValueValidator(1)],
    )
    unit_price = models.DecimalField(
        _('unit price'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    class Meta:
        verbose_name = _('order item')
        verbose_name_plural = _('order items')
        ordering = ['id']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['seller']),
            models.Index(fields=['product']),
        ]

    def __str__(self):
        product_name = self.product.name if self.product else _('Deleted product')
        return f'{self.quantity}x {product_name}'

    @property
    def subtotal(self):
        return self.unit_price * self.quantity
