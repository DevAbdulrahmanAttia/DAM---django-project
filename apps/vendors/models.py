from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Seller(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='seller_profile',
        verbose_name=_('user'),
    )
    store_name = models.CharField(_('store name'), max_length=255, db_index=True)
    description = models.TextField(_('description'), blank=True)
    logo = models.ImageField(_('logo'), upload_to='sellers/%Y/%m/', blank=True, null=True)
    is_approved = models.BooleanField(
        _('approved'),
        default=False,
        db_index=True,
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('seller')
        verbose_name_plural = _('sellers')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['store_name']),
            models.Index(fields=['is_approved', '-created_at']),
        ]

    def __str__(self):
        return self.store_name
