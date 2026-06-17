from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.products.models import Category, Product
from apps.vendors.models import Seller

User = get_user_model()

DEMO_PRODUCTS = [
    {
        'name': 'Wireless Headphones',
        'slug': 'wireless-headphones',
        'description': 'Noise-cancelling over-ear headphones with 30h battery.',
        'price': Decimal('89.99'),
        'stock': 25,
    },
    {
        'name': 'Smart Watch',
        'slug': 'smart-watch',
        'description': 'Fitness tracking smart watch with heart-rate monitor.',
        'price': Decimal('149.50'),
        'stock': 15,
    },
    {
        'name': 'USB-C Hub',
        'slug': 'usb-c-hub',
        'description': '7-in-1 USB-C hub with HDMI and SD card reader.',
        'price': Decimal('34.99'),
        'stock': 40,
    },
    {
        'name': 'Mechanical Keyboard',
        'slug': 'mechanical-keyboard',
        'description': 'RGB mechanical keyboard with blue switches.',
        'price': Decimal('79.00'),
        'stock': 20,
    },
]


class Command(BaseCommand):
    help = 'Seed demo category, seller profile, and products for cart/order testing.'

    def handle(self, *args, **options):
        category, _ = Category.objects.get_or_create(
            slug='electronics',
            defaults={
                'name': 'Electronics',
                'description': 'Gadgets and electronic accessories.',
            },
        )
        self.stdout.write(self.style.SUCCESS(f'Category: {category.name}'))

        seller_user = User.objects.filter(username='seller').first()
        if seller_user is None:
            self.stdout.write(
                self.style.ERROR('Seller user not found. Run: python manage.py seed_users')
            )
            return

        seller, _ = Seller.objects.get_or_create(
            user=seller_user,
            defaults={
                'store_name': 'Demo Electronics Store',
                'description': 'Official demo seller for development.',
                'is_approved': True,
            },
        )
        if not seller.is_approved:
            seller.is_approved = True
            seller.save(update_fields=['is_approved'])

        self.stdout.write(self.style.SUCCESS(f'Seller: {seller.store_name}'))

        for item in DEMO_PRODUCTS:
            product, created = Product.objects.update_or_create(
                slug=item['slug'],
                defaults={
                    'seller': seller,
                    'category': category,
                    'name': item['name'],
                    'description': item['description'],
                    'price': item['price'],
                    'stock': item['stock'],
                    'is_active': True,
                },
            )
            action = 'Created' if created else 'Updated'
            self.stdout.write(
                self.style.SUCCESS(f'{action} product: {product.name} (${product.price})')
            )

        self.stdout.write(self.style.SUCCESS('Catalog seeding complete.'))
