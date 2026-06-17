from django.db import models
from django.utils.translation import gettext_lazy as _


class Banner(models.Model):
    title = models.CharField(_('title'), max_length=255)
    subtitle = models.CharField(_('subtitle'), max_length=500, blank=True)
    image = models.ImageField(_('image'), upload_to='banners/%Y/%m/')
    link_url = models.URLField(_('link URL'), blank=True)
    button_text = models.CharField(_('button text'), max_length=100, blank=True, default='Shop Now')
    order = models.PositiveIntegerField(_('display order'), default=0, db_index=True)
    is_active = models.BooleanField(_('active'), default=True, db_index=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('banner')
        verbose_name_plural = _('banners')
        ordering = ['order', '-created_at']
        indexes = [
            models.Index(fields=['is_active', 'order']),
        ]

    def __str__(self):
        return self.title
