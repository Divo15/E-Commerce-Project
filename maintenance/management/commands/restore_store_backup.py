from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from maintenance.backups import require_private_location, restore_backup


class Command(BaseCommand):
    help = 'Restore a verified snapshot into a NEW directory. Never overwrites the live store.'

    def add_arguments(self, parser):
        parser.add_argument('archive')
        parser.add_argument('--destination', type=Path, required=True)

    def handle(self, *args, **options):
        require_private_location(options['destination'], settings.MEDIA_ROOT, settings.STATIC_ROOT)
        destination = restore_backup(options['archive'], options['destination'])
        self.stdout.write(self.style.SUCCESS(f'Restored and verified: {destination}'))
        self.stdout.write('Live settings were not changed. Stop the app before switching DJANGO_DATA_DIR to this directory.')
