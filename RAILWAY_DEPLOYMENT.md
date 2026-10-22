# Railway deployment progress

The running app has static-file serving, Gunicorn, and PostgreSQL URL support.
It is NOT yet a completed production deployment or a copy of the existing store.

## Database connection

Add a PostgreSQL service in the same Railway project/environment. In the web
service, add DATABASE_URL as a reference to that service's DATABASE_URL, for
example `${{Postgres.DATABASE_URL}}` if the service is named Postgres. Use the
private internal URL within Railway; keep the value out of Git and screenshots.
The startup command migrates the selected database before Gunicorn starts.
Without DATABASE_URL the app still uses SQLite, including on Railway. Do not
enter real customer data in that temporary cloud database.

## Existing store transfer

Preserve a verified local backup before migration. Import existing accounts,
products, categories, inventory, saved carts and hero poster records into an
empty PostgreSQL database only. Copy uploaded files with their original relative
paths to permanent photo storage. Never commit database dumps or photos to Git.
Verify record counts, product/hero images, original admin permissions and Google
sign-in before accepting live traffic. Do not rerun an initial import against a
populated live database or reset customer/admin passwords during the transfer.

## Remaining launch work

- Web service volume: mount /data and set DJANGO_DATA_DIR=/data. Catalogue-referenced
  images are served from /media/ with DEBUG=false; other files are not public.
  Keep one app replica while photos use this volume. Move photos to object storage
  before horizontal scaling.
- Set a stable private DJANGO_SECRET_KEY, DJANGO_DEBUG=false, allowed hosts,
  CSRF origins, trusted proxy configuration and public origin for the final domain.
- Production currently requires DJANGO_DATA_DIR to point to persistent storage.
- Set Google client credentials as Railway secrets and register exact callback URLs.
- Configure PostgreSQL backups and independent offsite backups of database/photos.
  The existing backup_store command supports local SQLite, not PostgreSQL or buckets.
- Test an actual restore and the account/cart/WhatsApp purchase flow.
- Connect shalicollections.com only after launch checks are complete.
