from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from core.models import UserProfile


class Command(BaseCommand):
    help = 'Create missing UserProfile records for existing users.'

    def handle(self, *args, **options):
        created_count = 0
        users_without_profile = User.objects.filter(profile__isnull=True)
        for user in users_without_profile.iterator():
            _, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={'display_name': user.get_full_name() or user.username},
            )
            if created:
                created_count += 1
        self.stdout.write(self.style.SUCCESS(f'Backfill complete. Created {created_count} profiles.'))
