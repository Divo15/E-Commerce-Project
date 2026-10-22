"""Verified SQLite/media snapshots and non-destructive recovery."""
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sqlite3
import stat
from tempfile import TemporaryDirectory
from uuid import uuid4
from zipfile import BadZipFile, ZIP_DEFLATED, ZipFile

from django.core.management.base import CommandError

FORMAT = 'shali-store-backup-v1'
CHUNK = 1024 * 1024
MEDIA_COLUMNS = {
    'store_product': ('image_1', 'image_2', 'image_3'),
    'category_category': ('category_image',),
    'category_heroposter': ('image',),
}


def _readonly(path):
    return sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True, timeout=30)


def check_database(path):
    with closing(_readonly(path)) as database:
        if database.execute('PRAGMA quick_check').fetchall() != [('ok',)]:
            raise CommandError('Database integrity check failed.')
        if database.execute('PRAGMA foreign_key_check').fetchone():
            raise CommandError('Database has inconsistent relationships.')


def _media_references(database_path):
    result = set()
    with closing(_readonly(database_path)) as database:
        tables = {row[0] for row in database.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for table, columns in MEDIA_COLUMNS.items():
            if table not in tables:
                continue
            # Identifiers come exclusively from the fixed table/column list above.
            for row in database.execute(f'SELECT {", ".join(columns)} FROM {table}'):
                result.update(str(value) for value in row if value)
    return result


def _safe_name(name):
    path = PurePosixPath(name)
    if not name or '\\' in name or ':' in name or path.is_absolute() or '..' in path.parts or str(path) != name:
        raise CommandError('Backup contains an unsafe file path.')
    if name != 'db.sqlite3' and not (name.startswith('media/') and len(path.parts) > 1):
        raise CommandError('Backup contains an unexpected file.')
    return name


def _private_directory(path):
    path = Path(path).resolve()
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    return path


def _outside_media(destination, media):
    if Path(destination).resolve().is_relative_to(Path(media).resolve()):
        raise CommandError('Backups must not be stored in the public media directory.')


def require_private_location(destination, *public_roots):
    if any(Path(destination).resolve().is_relative_to(Path(root).resolve()) for root in public_roots if root):
        raise CommandError('Store data and backups must not be placed in public media/static directories.')


def verify_backup(archive_path):
    """Check every payload hash, the database and every referenced image."""
    try:
        with ZipFile(archive_path) as archive:
            entries = archive.infolist()
            names = [entry.filename for entry in entries]
            if len(names) != len(set(names)) or 'manifest.json' not in names:
                raise CommandError('Backup has duplicate entries or no manifest.')
            manifest_info = archive.getinfo('manifest.json')
            if manifest_info.file_size > 4 * CHUNK:
                raise CommandError('Backup manifest is too large.')
            manifest = json.loads(archive.read(manifest_info))
            files = manifest.get('files')
            if manifest.get('format') != FORMAT or not isinstance(files, dict) or 'db.sqlite3' not in files:
                raise CommandError('Unrecognized backup format.')
            created = datetime.fromisoformat(manifest['created_at'])
            if created.tzinfo is None:
                raise CommandError('Backup timestamp must include a timezone.')
            if set(names) != set(files) | {'manifest.json'}:
                raise CommandError('Backup contents do not match its manifest.')
            with TemporaryDirectory(prefix='shali-verify-') as temporary:
                database_path = Path(temporary) / 'db.sqlite3'
                for name, expected in files.items():
                    _safe_name(name)
                    info = archive.getinfo(name)
                    if info.is_dir() or stat.S_ISLNK(info.external_attr >> 16):
                        raise CommandError('Backup must contain ordinary files only.')
                    if info.file_size != expected['size']:
                        raise CommandError('Backup file size does not match.')
                    digest, size = hashlib.sha256(), 0
                    with archive.open(info) as source:
                        target = database_path.open('wb') if name == 'db.sqlite3' else None
                        try:
                            while block := source.read(CHUNK):
                                digest.update(block)
                                size += len(block)
                                if target:
                                    target.write(block)
                        finally:
                            if target:
                                target.close()
                    if size != expected['size'] or digest.hexdigest() != expected['sha256']:
                        raise CommandError('Backup checksum verification failed.')
                check_database(database_path)
                missing = {f'media/{name}' for name in _media_references(database_path)} - set(files)
                if missing:
                    raise CommandError(f'Backup is missing {len(missing)} referenced image(s).')
            return manifest
    except CommandError:
        raise
    except (OSError, BadZipFile, ValueError, KeyError, TypeError, AttributeError, sqlite3.Error):
        raise CommandError('Backup could not be verified; it was not restored.') from None


def create_backup(database_path, media_root, output_dir, replica_dir=None):
    database_path, media_root = Path(database_path).resolve(), Path(media_root).resolve()
    if not database_path.is_file():
        raise CommandError('Database file does not exist; refusing to back up an empty store.')
    _outside_media(output_dir, media_root)
    if replica_dir:
        _outside_media(replica_dir, media_root)
    output_dir = _private_directory(output_dir)
    created = datetime.now(timezone.utc)
    name = f'shali-{created:%Y%m%dT%H%M%S}-{uuid4().hex[:8]}.zip'
    with TemporaryDirectory(prefix='.shali-backup-', dir=output_dir) as temporary:
        temporary = Path(temporary)
        snapshot = temporary / 'db.sqlite3'
        with closing(_readonly(database_path)) as source, closing(sqlite3.connect(snapshot)) as destination:
            # SQLite's online backup API produces a consistent committed snapshot,
            # including changes in WAL, without copying a live database file.
            source.backup(destination)
        check_database(snapshot)
        payload = [('db.sqlite3', snapshot)]
        if media_root.exists():
            for path in sorted(media_root.rglob('*')):
                if path.is_symlink():
                    raise CommandError('Media symlinks are not supported by backups.')
                if path.is_file():
                    payload.append(('media/' + path.relative_to(media_root).as_posix(), path))
        manifest = {'format': FORMAT, 'created_at': created.isoformat(), 'files': {}}
        pending = temporary / name
        with ZipFile(pending, 'w', compression=ZIP_DEFLATED, compresslevel=1) as archive:
            for archive_name, path in payload:
                _safe_name(archive_name)
                before = path.stat()
                digest, size = hashlib.sha256(), 0
                with path.open('rb') as source, archive.open(archive_name, 'w') as destination:
                    while block := source.read(CHUNK):
                        digest.update(block)
                        destination.write(block)
                        size += len(block)
                after = path.stat()
                if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns) or size != before.st_size:
                    raise CommandError('A media file changed during backup. Please retry.')
                manifest['files'][archive_name] = {'size': size, 'sha256': digest.hexdigest()}
            archive.writestr('manifest.json', json.dumps(manifest, indent=2))
        verify_backup(pending)
        os.chmod(pending, 0o600)
        final = output_dir / name
        os.replace(pending, final)
    if replica_dir and Path(replica_dir).resolve() != output_dir:
        replica_dir = _private_directory(replica_dir)
        with TemporaryDirectory(prefix='.shali-replica-', dir=replica_dir) as temporary:
            replica = Path(temporary) / name
            shutil.copyfile(final, replica)
            verify_backup(replica)
            os.chmod(replica, 0o600)
            os.replace(replica, replica_dir / name)
    return final


def restore_backup(archive_path, destination):
    """Restore only to a new directory, never over the live store."""
    destination = Path(destination).resolve()
    if destination.exists():
        raise CommandError('Restore destination already exists. Choose a new directory; existing data was not changed.')
    manifest = verify_backup(archive_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix='.shali-restore-', dir=destination.parent) as temporary:
        restored = Path(temporary) / 'store'
        restored.mkdir(mode=0o700)
        with ZipFile(archive_path) as archive:
            for name in manifest['files']:
                _safe_name(name)
                target = restored / name
                target.parent.mkdir(parents=True, exist_ok=True)
                digest, size = hashlib.sha256(), 0
                with archive.open(name) as source, target.open('xb') as output:
                    while block := source.read(CHUNK):
                        output.write(block)
                        digest.update(block)
                        size += len(block)
                expected = manifest['files'][name]
                if size != expected['size'] or digest.hexdigest() != expected['sha256']:
                    raise CommandError('Backup changed during restore; destination was not created.')
                os.chmod(target, 0o600)
        (restored / 'media').mkdir(exist_ok=True)
        check_database(restored / 'db.sqlite3')
        (restored / '.shali-storage.json').write_text(json.dumps({'format': FORMAT, 'restored_from': Path(archive_path).name, 'created_at': manifest['created_at']}), encoding='utf-8')
        # rename refuses to merge into an existing non-empty destination.
        restored.rename(destination)
    return destination
