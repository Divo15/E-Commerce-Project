from django.core.management.base import BaseCommand

from maintenance.backups import verify_backup


class Command(BaseCommand):
    help = 'Verify a store backup without changing live data.'

    def add_arguments(self, parser):
        parser.add_argument('archive')

    def handle(self, *args, **options):
        manifest = verify_backup(options['archive'])
        self.stdout.write(self.style.SUCCESS(f"Backup verified: database and {len(manifest['files']) - 1} uploaded files."))
