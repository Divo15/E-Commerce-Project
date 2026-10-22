from datetime import datetime, timezone
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from maintenance.backups import create_backup, require_private_location, verify_backup


class Command(BaseCommand):
    help = 'Create and verify a private snapshot of the store database and uploaded photos.'

    def add_arguments(self, parser):
        parser.add_argument('--output-dir', type=Path)
        parser.add_argument('--if-older-than-hours', type=float, default=0)

    def handle(self, *args, **options):
        database = settings.DATABASES['default']
        if database['ENGINE'] != 'django.db.backends.sqlite3':
            raise CommandError('This command supports SQLite. Use managed database backups for other database engines.')
        output = options['output_dir'] or settings.BACKUP_ROOT
        require_private_location(output, settings.MEDIA_ROOT, settings.STATIC_ROOT)
        if settings.BACKUP_REPLICA_ROOT:
            require_private_location(settings.BACKUP_REPLICA_ROOT, settings.MEDIA_ROOT, settings.STATIC_ROOT)
        hours = options['if_older_than_hours']
        if hours < 0:
            raise CommandError('Backup interval must not be negative.')
        if hours:
            previous = sorted(Path(output).glob('shali-*.zip'), key=lambda path: path.stat().st_mtime, reverse=True)
            if previous:
                try:
                    manifest = verify_backup(previous[0])
                    age = (datetime.now(timezone.utc) - datetime.fromisoformat(manifest['created_at'])).total_seconds() / 3600
                    if 0 <= age < hours:
                        self.stdout.write('A recent verified backup already exists; no new snapshot was needed.')
                        return
                except CommandError:
                    # A damaged previous snapshot must not prevent a fresh backup.
                    pass
        try:
            archive = create_backup(database['NAME'], settings.MEDIA_ROOT, output, settings.BACKUP_REPLICA_ROOT)
        except (OSError, ValueError) as error:
            raise CommandError('Backup failed; no incomplete snapshot was published.') from error
        self.stdout.write(self.style.SUCCESS(f'Backup created and verified: {archive}'))
