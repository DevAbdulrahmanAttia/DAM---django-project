from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserRole(models.TextChoices):
    CUSTOMER = 'customer', _('Customer')
    SELLER = 'seller', _('Seller')
    ADMIN = 'admin', _('Admin')


class User(AbstractUser):
    email = models.EmailField(
        _('email address'),
        unique=True,
        db_index=True,
    )
    phone = models.CharField(
        _('phone number'),
        max_length=20,
        unique=True,
        db_index=True,
    )
    role = models.CharField(
        _('role'),
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.CUSTOMER,
        db_index=True,
    )
    is_verified = models.BooleanField(
        _('verified'),
        default=False,
        db_index=True,
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['phone']),
            models.Index(fields=['role', 'is_active']),
        ]

    def __str__(self):
        return self.username


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_('user'),
    )
    full_name = models.CharField(_('full name'), max_length=255, blank=True, db_index=True)
    address = models.TextField(_('address'), blank=True)
    city = models.CharField(_('city'), max_length=100, blank=True, db_index=True)
    country = models.CharField(_('country'), max_length=100, blank=True, db_index=True)
    profile_image = models.ImageField(
        _('profile image'),
        upload_to='profiles/%Y/%m/',
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')
        ordering = ['full_name']
        indexes = [
            models.Index(fields=['full_name']),
            models.Index(fields=['city', 'country']),
        ]

    def __str__(self):
        return self.full_name
