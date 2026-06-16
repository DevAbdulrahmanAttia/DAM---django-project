from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    name = models.CharField(_('name'), max_length=255, db_index=True)
    slug = models.SlugField(_('slug'), max_length=255, unique=True, db_index=True)
    description = models.TextField(_('description'), blank=True)

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.name


class Product(models.Model):
    seller = models.ForeignKey(
        'vendors.Seller',
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name=_('seller'),
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name=_('category'),
    )
    name = models.CharField(_('name'), max_length=255, db_index=True)
    slug = models.SlugField(_('slug'), max_length=255, unique=True, db_index=True)
    description = models.TextField(_('description'))
    price = models.DecimalField(
        _('price'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    stock = models.PositiveIntegerField(_('stock'), default=0)
    is_active = models.BooleanField(_('active'), default=True, db_index=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('product')
        verbose_name_plural = _('products')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['slug']),
            models.Index(fields=['seller', 'is_active']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_('product'),
    )
    image = models.ImageField(_('image'), upload_to='products/%Y/%m/')
    is_primary = models.BooleanField(_('primary'), default=False, db_index=True)

    class Meta:
        verbose_name = _('product image')
        verbose_name_plural = _('product images')
        ordering = ['-is_primary', 'id']
        indexes = [
            models.Index(fields=['product', 'is_primary']),
        ]

    def __str__(self):
        return f'{self.product.name} - Image {self.pk}'


class Review(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('product'),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('user'),
    )
    rating = models.PositiveSmallIntegerField(
        _('rating'),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        db_index=True,
    )
    comment = models.TextField(_('comment'), blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('review')
        verbose_name_plural = _('reviews')
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'user'],
                name='unique_review_per_user_per_product',
            ),
        ]
        indexes = [
            models.Index(fields=['product', '-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['rating']),
        ]

    def __str__(self):
        return f'{self.user} - {self.product.name} ({self.rating}/5)'


class Wishlist(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wishlist_items',
        verbose_name=_('user'),
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='wishlisted_by',
        verbose_name=_('product'),
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('wishlist item')
        verbose_name_plural = _('wishlist items')
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'product'],
                name='unique_wishlist_item_per_user',
            ),
        ]
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['product']),
        ]

    def __str__(self):
        return f'{self.user} - {self.product.name}'
