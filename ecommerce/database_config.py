"""Use Railway PostgreSQL when configured; preserve local SQLite otherwise."""
import dj_database_url
from django.core.exceptions import ImproperlyConfigured


def database_config(url, data_root):
    if not url:
        return {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': data_root / 'db.sqlite3',
            'OPTIONS': {'timeout': 20},
        }
    try:
        database = dj_database_url.parse(url, conn_max_age=60, conn_health_checks=True)
        if database['ENGINE'] != 'django.db.backends.postgresql' or not database.get('NAME') or not database.get('HOST'):
            raise ValueError
    except (ValueError, KeyError, TypeError):
        raise ImproperlyConfigured('DATABASE_URL must be a valid PostgreSQL connection URL.') from None
    return database
