import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from maintenance.backups import create_backup, require_private_location, restore_backup


class Command(BaseCommand):
    help = 'Copy existing store data to a new permanent directory through a verified backup. Stop the web server first.'

    def add_arguments(self, parser):
        parser.add_argument('--destination', type=Path, required=True)
        parser.add_argument('--backup-dir', type=Path, required=True)
        parser.add_argument('--activate-local', action='store_true')

    def handle(self, *args, **options):
        destination = options['destination'].resolve()
        backup_dir = options['backup_dir'].resolve()
        if not options['destination'].is_absolute() or not options['backup_dir'].is_absolute():
            raise CommandError('Use absolute directory paths.')
        if destination.exists():
            raise CommandError('Destination already exists. No existing data was changed.')
        require_private_location(destination, settings.MEDIA_ROOT, settings.STATIC_ROOT)
        require_private_location(backup_dir, settings.MEDIA_ROOT, settings.STATIC_ROOT)
        if backup_dir.is_relative_to(destination) or destination.is_relative_to(backup_dir):
            raise CommandError('For this copy, choose separate data and backup directories.')
        if options['activate_local'] and (not settings.DEBUG or os.environ.get('DJANGO_DATA_DIR')):
            raise CommandError('Local activation is only for local development without DJANGO_DATA_DIR. Set production environment variables on your host.')
        database = settings.DATABASES['default']
        if database['ENGINE'] != 'django.db.backends.sqlite3':
            raise CommandError('This migration command supports SQLite only.')
        archive = create_backup(database['NAME'], settings.MEDIA_ROOT, backup_dir, settings.BACKUP_REPLICA_ROOT)
        restore_backup(archive, destination)
        if options['activate_local']:
            config_dir = Path(settings.BASE_DIR) / '.local'
            config_dir.mkdir(exist_ok=True)
            with TemporaryDirectory(prefix='storage-', dir=config_dir) as temporary:
                config = Path(temporary) / 'storage.json'
                config.write_text(json.dumps({'data_dir': str(destination), 'backup_dir': str(backup_dir)}, indent=2), encoding='utf-8')
                os.replace(config, config_dir / 'storage.json')
        self.stdout.write(self.style.SUCCESS(f'Data copied and verified: {destination}'))
        self.stdout.write(f'Backup retained: {archive}')
        self.stdout.write('Original database and photos were left untouched. Restart the server to use the configured location.')
