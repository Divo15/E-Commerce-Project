from pathlib import Path
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase
from .database_config import database_config


class DatabaseConfigurationTests(SimpleTestCase):
    def test_local_data_still_uses_sqlite(self):
        data = Path('/persistent-data')
        result = database_config('', data)
        self.assertEqual(result['ENGINE'], 'django.db.backends.sqlite3')
        self.assertEqual(result['NAME'], data / 'db.sqlite3')

    def test_railway_postgres_url_and_encoded_password(self):
        result = database_config('postgresql://store:example%40secret@postgres.railway.internal:5432/railway', Path('/data'))
        self.assertEqual(result['ENGINE'], 'django.db.backends.postgresql')
        self.assertEqual(result['PASSWORD'], 'example@secret')
        self.assertEqual(result['HOST'], 'postgres.railway.internal')
        self.assertEqual(result['CONN_MAX_AGE'], 60)
        self.assertTrue(result['CONN_HEALTH_CHECKS'])
        self.assertNotIn('timeout', result.get('OPTIONS', {}))

    def test_invalid_connection_never_falls_back_to_empty_sqlite(self):
        for url in ['not-a-url', 'postgres://user:secret@host/', 'sqlite:///accidental.db', 'mysql://user:secret@host/store']:
            with self.subTest(url=url), self.assertRaises(ImproperlyConfigured):
                database_config(url, Path('/data'))

    def test_error_does_not_expose_credentials(self):
        with self.assertRaises(ImproperlyConfigured) as result:
            database_config('unsupported://user:private-password@host/store', Path('/data'))
        self.assertNotIn('private-password', str(result.exception))
