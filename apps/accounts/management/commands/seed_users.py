from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.accounts.models import UserProfile, UserRole

User = get_user_model()

DEFAULT_PASSWORD = 'Dam@123456'

SEED_USERS = [
    {
        'username': 'admin',
        'email': 'admin@dam.test',
        'phone': '+10000000001',
        'role': UserRole.ADMIN,
        'is_staff': True,
        'is_superuser': True,
        'profile': {
            'full_name': 'System Admin',
            'city': 'Cairo',
            'country': 'Egypt',
        },
    },
    {
        'username': 'customer',
        'email': 'customer@dam.test',
        'phone': '+10000000002',
        'role': UserRole.CUSTOMER,
        'profile': {
            'full_name': 'Demo Customer',
            'address': '123 Nile Street',
            'city': 'Cairo',
            'country': 'Egypt',
        },
    },
    {
        'username': 'seller',
        'email': 'seller@dam.test',
        'phone': '+10000000003',
        'role': UserRole.SELLER,
        'profile': {
            'full_name': 'Demo Seller',
            'address': '45 Market Road',
            'city': 'Alexandria',
            'country': 'Egypt',
        },
    },
]


class Command(BaseCommand):
    help = 'Seed default admin, customer, and seller users for local development.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            default=DEFAULT_PASSWORD,
            help=f'Password for all seeded users (default: {DEFAULT_PASSWORD})',
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete seeded users before recreating them.',
        )

    def handle(self, *args, **options):
        password = options['password']
        usernames = [entry['username'] for entry in SEED_USERS]

        if options['reset']:
            deleted, _ = User.objects.filter(username__in=usernames).delete()
            self.stdout.write(self.style.WARNING(f'Removed {deleted} existing seeded record(s).'))

        for raw_entry in SEED_USERS:
            entry = {**raw_entry}
            profile_data = entry.pop('profile', {})
            username = entry['username']

            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    **entry,
                    'is_verified': True,
                },
            )

            if not created:
                for field, value in entry.items():
                    setattr(user, field, value)
                user.is_verified = True
                user.set_password(password)
                user.save()
                action = 'Updated'
            else:
                user.set_password(password)
                user.save()
                action = 'Created'

            profile, _ = UserProfile.objects.get_or_create(user=user)
            for field, value in profile_data.items():
                setattr(profile, field, value)
            profile.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f'{action} {user.role} user "{username}" ({user.email})'
                )
            )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Seeding complete. Default credentials:'))
        self.stdout.write(f'  Password (all users): {password}')
        for entry in SEED_USERS:
            self.stdout.write(
                f'  - {entry["role"]}: {entry["username"]} / {entry["email"]}'
            )
