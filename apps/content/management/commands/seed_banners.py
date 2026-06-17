from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile

from apps.content.models import Banner


BANNER_DATA = [
    {
        'title': 'Summer Collection 2026',
        'subtitle': 'Discover the latest trends with up to 40% off on selected items',
        'button_text': 'Shop Now',
        'order': 1,
    },
    {
        'title': 'New Arrivals',
        'subtitle': 'Fresh products from top sellers across the marketplace',
        'button_text': 'Explore',
        'order': 2,
    },
    {
        'title': 'Free Shipping',
        'subtitle': 'On all orders over $50 — limited time offer',
        'button_text': 'Learn More',
        'order': 3,
    },
]


def _placeholder_svg(title: str, color: str) -> bytes:
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="500" viewBox="0 0 1400 500">
  <defs>
    <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{color};stop-opacity:1"/>
      <stop offset="100%" style="stop-color:#0f172a;stop-opacity:1"/>
    </linearGradient>
  </defs>
  <rect width="1400" height="500" fill="url(#g)"/>
  <text x="700" y="260" font-family="Arial,sans-serif" font-size="48" fill="white" text-anchor="middle" font-weight="bold">{title}</text>
</svg>'''
    return svg.encode('utf-8')


class Command(BaseCommand):
    help = 'Seed homepage banners with placeholder images'

    def handle(self, *args, **options):
        colors = ['#1e40af', '#f97316', '#059669']
        created = 0

        for idx, data in enumerate(BANNER_DATA):
            banner, was_created = Banner.objects.get_or_create(
                title=data['title'],
                defaults={
                    'subtitle': data['subtitle'],
                    'button_text': data['button_text'],
                    'order': data['order'],
                    'is_active': True,
                },
            )
            if was_created or not banner.image:
                color = colors[idx % len(colors)]
                filename = f"banner-{banner.pk or idx + 1}.svg"
                banner.image.save(filename, ContentFile(_placeholder_svg(data['title'], color)), save=True)
                created += 1
                self.stdout.write(self.style.SUCCESS(f'Banner ready: {banner.title}'))
            else:
                self.stdout.write(f'Banner exists: {banner.title}')

        self.stdout.write(self.style.SUCCESS(f'Done. {created} banner(s) created/updated.'))
