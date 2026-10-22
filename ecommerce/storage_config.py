"""Keep application data separate from deployable source code."""
import json
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured


def storage_paths(base_dir, debug, environ):
    local = {}
    config_file = base_dir / '.local' / 'storage.json'
    if debug and config_file.is_file():
        try:
            local = json.loads(config_file.read_text(encoding='utf-8'))
            if not isinstance(local, dict):
                raise ValueError
        except (OSError, ValueError):
            raise ImproperlyConfigured('Invalid local storage configuration.') from None
    configured = environ.get('DJANGO_DATA_DIR')
    if not debug and not configured:
        raise ImproperlyConfigured('DJANGO_DATA_DIR must point to a mounted persistent directory in production.')
    data = Path(configured or local.get('data_dir') or base_dir).expanduser()
    backup = Path(environ.get('DJANGO_BACKUP_DIR') or local.get('backup_dir') or data / 'backups').expanduser()
    replica = environ.get('DJANGO_BACKUP_REPLICA_DIR', '')
    paths = [data, backup, *([Path(replica).expanduser()] if replica else [])]
    if any(not path.is_absolute() for path in paths):
        raise ImproperlyConfigured('Storage and backup directories must use absolute paths.')
    return data.resolve(), backup.resolve(), Path(replica).expanduser().resolve() if replica else None
