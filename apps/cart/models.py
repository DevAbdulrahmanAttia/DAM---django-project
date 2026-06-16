from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class Cart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='carts',
        verbose_name=_('user'),
        null=True,
        blank=True,
    )
    session_key = models.CharField(
        _('session key'),
        max_length=40,
        null=True,
        blank=True,
        db_index=True,
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('cart')
        verbose_name_plural = _('carts')
        ordering = ['-updated_at']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(user__isnull=False) | models.Q(session_key__isnull=False),
                name='cart_requires_user_or_session',
            ),
        ]
        indexes = [
            models.Index(fields=['user', '-updated_at']),
            models.Index(fields=['session_key']),
        ]

    def __str__(self):
        if self.user:
            return f'Cart for {self.user}'
        return f'Guest cart ({self.session_key})'


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('cart'),
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name=_('product'),
    )
    quantity = models.PositiveIntegerField(
        _('quantity'),
        default=1,
        validators=[MinValueValidator(1)],
    )
    unit_price = models.DecimalField(
        _('unit price'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    class Meta:
        verbose_name = _('cart item')
        verbose_name_plural = _('cart items')
        ordering = ['id']
        constraints = [
            models.UniqueConstraint(
                fields=['cart', 'product'],
                name='unique_product_per_cart',
            ),
        ]
        indexes = [
            models.Index(fields=['cart']),
            models.Index(fields=['product']),
        ]

    def __str__(self):
        return f'{self.quantity}x {self.product.name}'

    @property
    def subtotal(self):
        return self.unit_price * self.quantity
