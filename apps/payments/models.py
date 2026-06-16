from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class PaymentMethod(models.TextChoices):
    CREDIT_CARD = 'credit_card', _('Credit Card')
    PAYPAL = 'paypal', _('PayPal')
    CASH_ON_DELIVERY = 'cash_on_delivery', _('Cash on Delivery')
    WALLET = 'wallet', _('Wallet')


class PaymentStatus(models.TextChoices):
    PENDING = 'pending', _('Pending')
    SUCCESS = 'success', _('Success')
    FAILED = 'failed', _('Failed')


class Payment(models.Model):
    order = models.OneToOneField(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='payment',
        verbose_name=_('order'),
    )
    payment_method = models.CharField(
        _('payment method'),
        max_length=20,
        choices=PaymentMethod.choices,
        db_index=True,
    )
    transaction_id = models.CharField(
        _('transaction ID'),
        max_length=255,
        blank=True,
        db_index=True,
    )
    amount = models.DecimalField(
        _('amount'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True,
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('payment')
        verbose_name_plural = _('payments')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['payment_method', 'status']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f'Payment for Order #{self.order_id} - {self.get_status_display()}'
