from contextlib import closing
import hashlib
from io import StringIO
import json
import os
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from unittest import mock
from zipfile import ZIP_DEFLATED, ZipFile

from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, override_settings

from ecommerce.storage_config import storage_paths
from maintenance.backups import create_backup, restore_backup, verify_backup


class StoreBackupTests(SimpleTestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory(prefix='shali-storage-test-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.media = self.root / 'media'
        self.media.mkdir()
        (self.media / 'photos').mkdir()
        (self.media / 'photos/product.jpg').write_bytes(b'product photo bytes')
        (self.media / 'photos/category.jpg').write_bytes(b'category photo bytes')
        self.database = self.root / 'db.sqlite3'
        self.writer = sqlite3.connect(self.database)
        self.addCleanup(self.writer.close)
        self.writer.executescript('''
            PRAGMA journal_mode=WAL;
            PRAGMA foreign_keys=ON;
            CREATE TABLE accounts_account(id INTEGER PRIMARY KEY, email TEXT, password TEXT);
            CREATE TABLE carts_cart(id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES accounts_account(id));
            CREATE TABLE store_product(id INTEGER PRIMARY KEY, image_1 TEXT, image_2 TEXT, image_3 TEXT);
            CREATE TABLE carts_cartitem(id INTEGER PRIMARY KEY, cart_id INTEGER REFERENCES carts_cart(id), product_id INTEGER REFERENCES store_product(id), quantity INTEGER);
            CREATE TABLE category_category(id INTEGER PRIMARY KEY, category_image TEXT);
            CREATE TABLE category_heroposter(id INTEGER PRIMARY KEY, image TEXT);
            CREATE TABLE django_session(session_key TEXT PRIMARY KEY, session_data TEXT);
            INSERT INTO accounts_account VALUES (1, 'customer@example.invalid', 'hashed-password');
            INSERT INTO carts_cart VALUES (1, 1);
            INSERT INTO store_product VALUES (1, 'photos/product.jpg', '', '');
            INSERT INTO carts_cartitem VALUES (1, 1, 1, 3);
            INSERT INTO category_category VALUES (1, 'photos/category.jpg');
            INSERT INTO django_session VALUES ('test-session', 'saved-session');
        ''')
        self.writer.commit()
        (self.root / 'private-secret').write_text('never-back-up-this-secret', encoding='utf-8')
        self.output = self.root / 'private-backups'

    def backup(self, **kwargs):
        return create_backup(self.database, self.media, self.output, **kwargs)

    def rewrite(self, archive, changes):
        replacement = self.root / 'changed.zip'
        with ZipFile(archive) as source, ZipFile(replacement, 'w', compression=ZIP_DEFLATED) as target:
            payload = {name: source.read(name) for name in source.namelist()}
            changes(payload)
            for name, content in payload.items():
                target.writestr(name, content)
        return replacement

    def test_round_trip_preserves_accounts_saved_cart_sessions_and_every_photo(self):
        archive = self.backup()
        manifest = verify_backup(archive)
        self.assertEqual(set(manifest['files']), {'db.sqlite3', 'media/photos/product.jpg', 'media/photos/category.jpg'})
        destination = restore_backup(archive, self.root / 'restored')
        with closing(sqlite3.connect(destination / 'db.sqlite3')) as database:
            self.assertEqual(database.execute('SELECT email, password FROM accounts_account').fetchone(), ('customer@example.invalid', 'hashed-password'))
            self.assertEqual(database.execute('SELECT user_id FROM carts_cart').fetchone(), (1,))
            self.assertEqual(database.execute('SELECT quantity FROM carts_cartitem').fetchone(), (3,))
            self.assertEqual(database.execute('SELECT session_data FROM django_session').fetchone(), ('saved-session',))
        self.assertEqual((destination / 'media/photos/product.jpg').read_bytes(), b'product photo bytes')
        self.assertFalse((destination / 'private-secret').exists())
        self.assertTrue((self.root / 'private-secret').exists())

    def test_online_snapshot_includes_committed_changes_still_in_wal(self):
        self.writer.execute("INSERT INTO accounts_account VALUES (2, 'new@example.invalid', 'another-hash')")
        self.writer.commit()
        self.assertTrue(Path(str(self.database) + '-wal').exists())
        destination = restore_backup(self.backup(), self.root / 'wal-restored')
        with closing(sqlite3.connect(destination / 'db.sqlite3')) as database:
            self.assertEqual(database.execute('SELECT COUNT(*) FROM accounts_account').fetchone()[0], 2)

    def test_corrupt_media_fails_verification_and_never_creates_restore_destination(self):
        archive = self.rewrite(self.backup(), lambda files: files.update({'media/photos/product.jpg': b'changed photo bytes'}))
        destination = self.root / 'bad-restore'
        with self.assertRaises(CommandError):
            restore_backup(archive, destination)
        self.assertFalse(destination.exists())

    def test_archive_cannot_escape_restore_directory(self):
        def insert_unsafe_path(files):
            name = 'media/../../escaped.txt'
            files[name] = b'unsafe'
            manifest = json.loads(files['manifest.json'])
            manifest['files'][name] = {'size': 6, 'sha256': hashlib.sha256(b'unsafe').hexdigest()}
            files['manifest.json'] = json.dumps(manifest).encode()
        archive = self.rewrite(self.backup(), insert_unsafe_path)
        with self.assertRaises(CommandError):
            restore_backup(archive, self.root / 'unsafe-restore')
        self.assertFalse((self.root / 'escaped.txt').exists())

    def test_restore_refuses_to_overwrite_live_files(self):
        archive = self.backup()
        before = self.database.read_bytes()
        with self.assertRaises(CommandError):
            restore_backup(archive, self.root)
        self.assertEqual(self.database.read_bytes(), before)
        self.assertEqual((self.media / 'photos/product.jpg').read_bytes(), b'product photo bytes')

    def test_missing_referenced_photo_does_not_publish_incomplete_snapshot(self):
        (self.media / 'photos/product.jpg').unlink()
        with self.assertRaisesMessage(CommandError, 'missing 1 referenced image'):
            self.backup()
        self.assertEqual(list(self.output.glob('shali-*.zip')), [])

    def test_backup_destination_must_not_be_public(self):
        with self.assertRaisesMessage(CommandError, 'public media'):
            create_backup(self.database, self.media, self.media / 'backups')
        self.assertFalse((self.media / 'backups').exists())

    def test_media_symlinks_cannot_copy_files_from_outside_uploads(self):
        link = self.media / 'leaked-secret'
        try:
            link.symlink_to(self.root / 'private-secret')
        except OSError:
            # Windows can restrict creating links; still exercise the rejection
            # branch without requiring elevated symlink privileges for tests.
            link.write_bytes(b'not a product image')
            with mock.patch.object(Path, 'is_symlink', lambda path: path.name == 'leaked-secret'):
                with self.assertRaisesMessage(CommandError, 'symlinks'):
                    self.backup()
            return
        with self.assertRaisesMessage(CommandError, 'symlinks'):
            self.backup()

    def test_optional_second_copy_is_verified_and_identical(self):
        replica = self.root / 'replica'
        archive = self.backup(replica_dir=replica)
        copied = replica / archive.name
        self.assertEqual(copied.read_bytes(), archive.read_bytes())
        self.assertEqual(verify_backup(copied)['format'], 'shali-store-backup-v1')

    def test_commands_refuse_private_data_under_static_files(self):
        static_root = self.root / 'static'
        with override_settings(STATIC_ROOT=static_root):
            with self.assertRaisesMessage(CommandError, 'public media/static'):
                call_command('backup_store', output_dir=static_root / 'backups', stdout=StringIO())
            with self.assertRaisesMessage(CommandError, 'public media/static'):
                call_command('restore_store_backup', 'unused.zip', destination=static_root / 'recovered', stdout=StringIO())
        self.assertFalse(static_root.exists())

    def test_backup_command_skips_only_a_recent_verified_snapshot(self):
        with override_settings(DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': self.database}}, MEDIA_ROOT=self.media, BACKUP_ROOT=self.output, BACKUP_REPLICA_ROOT=None):
            output = StringIO()
            call_command('backup_store', stdout=output)
            call_command('backup_store', if_older_than_hours=20, stdout=output)
            self.assertEqual(len(list(self.output.glob('shali-*.zip'))), 1)
            self.assertIn('recent verified backup', output.getvalue())
            next(self.output.glob('shali-*.zip')).write_bytes(b'damaged backup')
            call_command('backup_store', if_older_than_hours=20, stdout=output)
            self.assertEqual(len(list(self.output.glob('shali-*.zip'))), 2)

    def test_local_configuration_activates_only_after_verified_copy(self):
        destination = self.root / 'permanent'
        with override_settings(BASE_DIR=self.root, DEBUG=True, DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': self.database}}, MEDIA_ROOT=self.media, BACKUP_REPLICA_ROOT=None), mock.patch.dict(os.environ, {}, clear=True):
            call_command('configure_store_storage', destination=destination, backup_dir=self.output, activate_local=True, stdout=StringIO())
        config = json.loads((self.root / '.local/storage.json').read_text())
        self.assertEqual(Path(config['data_dir']), destination)
        self.assertTrue((destination / 'db.sqlite3').is_file())
        self.assertTrue(self.database.is_file())
        self.assertTrue((self.media / 'photos/product.jpg').is_file())


class PersistentStorageSettingsTests(SimpleTestCase):
    def test_production_requires_an_explicit_persistent_volume_path(self):
        with TemporaryDirectory() as temporary:
            base = Path(temporary)
            with self.assertRaisesMessage(ImproperlyConfigured, 'DJANGO_DATA_DIR'):
                storage_paths(base, False, {})
            with self.assertRaisesMessage(ImproperlyConfigured, 'absolute'):
                storage_paths(base, False, {'DJANGO_DATA_DIR': 'relative-data'})

    def test_production_data_location_stays_the_same_across_code_releases(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            environ = {'DJANGO_DATA_DIR': str(root / 'volume/store'), 'DJANGO_BACKUP_DIR': str(root / 'volume/backups')}
            first = storage_paths(root / 'release-one', False, environ)
            second = storage_paths(root / 'release-two', False, environ)
            self.assertEqual(first, second)
            self.assertEqual(first[0], root / 'volume/store')

    def test_local_pointer_survives_server_restarts_and_environment_can_override_it(self):
        with TemporaryDirectory() as temporary:
            base = Path(temporary)
            (base / '.local').mkdir()
            (base / '.local/storage.json').write_text(json.dumps({'data_dir': str(base / 'permanent'), 'backup_dir': str(base / 'backups')}))
            self.assertEqual(storage_paths(base, True, {}), storage_paths(base, True, {}))
            self.assertEqual(storage_paths(base, True, {})[0], base / 'permanent')
            self.assertEqual(storage_paths(base, True, {'DJANGO_DATA_DIR': str(base / 'override')})[0], base / 'override')
