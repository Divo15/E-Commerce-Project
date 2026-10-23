# Railway — current operations

Verified **23 October 2026 (Asia/Calcutta)**. Read [HANDOFF.md](HANDOFF.md) for full context/resource IDs, [CONTINUATION_GUIDE.md](CONTINUATION_GUIDE.md) for new-device setup.

## Already running

- Existing project carefree-optimism, production environment; repo Divo15/E-Commerce-Project, branch testing.
- Website https://e-commerce-project-production-6748.up.railway.app/, port 8080.
- Admin https://e-commerce-project-production-6748.up.railway.app/admin/.
- Private Postgres 18 service on postgres-volume; web service image volume at /data, media at /data/media.
- Original store migrated: 8 products, 5 saved posters (newest 3 active), 37 uploaded files, accounts/carts. Counts are a baseline and will change.
- Record equality and image checksums verified; 28 referenced images and 8 product links loaded. Restart persistence passed.
- Production DEBUG=false, secure cookies, HTTPS redirects and proxy configuration active; both inspected service configurations disable idle sleeping.

Not yet launch-complete: final DNS/certificate/forwarding, live Google callback checks, cloud/offsite backups and final flows/disclosures remain. Do not repeat the original import.

## Startup

railway.json contains:

```sh
python manage.py collectstatic --noinput && python manage.py migrate --noinput && gunicorn ecommerce.wsgi:application --bind 0.0.0.0:$PORT
```

Pinned dependencies include Gunicorn 26.2.0, WhiteNoise 6.12.0, dj-database-url 3.1.2, Psycopg binary 3.3.6. WhiteNoise handles /static/. ecommerce/media_views.py serves only catalogue-referenced uploaded images with DEBUG=false, protecting private/unreferenced/nonimage paths. Static collection is not an uploaded-media backup.

**Deadline:** Railway docs state legacy railway.json/railway.toml stops being read **1 December 2026**. Migrate this existing project to Railway IaC before then, reviewing the plan and preserving services, volumes and secrets. It has not been migrated. Source: https://docs.railway.com/infrastructure-as-code

## Variables

Private values already configured: DATABASE_URL, DJANGO_SECRET_KEY, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET. Keep them out of Git/chat. Signing key is stable.

```text
DJANGO_DEBUG=false
DJANGO_DATA_DIR=/data
DJANGO_TRUST_PROXY=true
ACCOUNT_PUBLIC_ORIGIN=https://e-commerce-project-production-6748.up.railway.app
WHATSAPP_ORDER_NUMBER=6583952511
DJANGO_ALLOWED_HOSTS=e-commerce-project-production-6748.up.railway.app,shalicollections.com,www.shalicollections.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://e-commerce-project-production-6748.up.railway.app,https://shalicollections.com,https://www.shalicollections.com
```

WEB-service DATABASE_URL references `${{Postgres.DATABASE_URL}}`; leave Postgres's generated connection variable intact. Without DATABASE_URL, code falls back to SQLite; never mistake that for the live DB. Production requires absolute persistent DJANGO_DATA_DIR for images even with PostgreSQL.

## DNS waiting on the client

The client owns GoDaddy and will edit DNS without sharing credentials. Chosen canonical domain: https://www.shalicollections.com/.

| Action | Type | Name | Value |
|---|---|---|---|
| Edit existing | CNAME | www | xyebi7xd.up.railway.app |
| Add | TXT | _railway-verify.www | railway-verify=ff1b8e7aaca0d129db38e493044938f37d96cfa6b72cb068dc6d76c0a4e79d36 |

Default TTL; preserve unrelated/mail records. At last check www still CNAMEs to shalicollections.com; ownership unverified and certificate validating ownership. Re-read status if the domain was recreated. The root domain also exists in Railway, but root CNAME @ is unsuitable for the chosen GoDaddy setup. Do not change nameservers.

After www DNS verifies and HTTPS works, forward bare shalicollections.com to https://www.shalicollections.com in GoDaddy: Permanent 301, forward only, no masking. Preserve www CNAME pointing at Railway, not @.

Google callbacks to add/verify in the EXISTING Web client:

```text
https://www.shalicollections.com/accounts/google/callback/
https://e-commerce-project-production-6748.up.railway.app/accounts/google/callback/
```

Original downloaded OAuth JSON lists root/ngrok only; not proof of current live Google settings. After DNS/callback configuration, set ACCOUNT_PUBLIC_ORIGIN=https://www.shalicollections.com and deploy. Login must start/finish on one origin; cookies do not transfer across domains.

## Read-only operations

```powershell
npx.cmd --yes @railway/cli@5.71.0 login
npx.cmd --yes @railway/cli@5.71.0 link --project 890fe855-842e-4f3c-8e53-1d7dcdabf8ac --environment production --service E-Commerce-Project
npx.cmd --yes @railway/cli@5.71.0 domain status www.shalicollections.com --service E-Commerce-Project --json
npx.cmd --yes @railway/cli@5.71.0 volume list --json
```

After SSH-key registration, direct domain-based access worked:

```sh
ssh -o BatchMode=yes -o ConnectTimeout=10 e-commerce-project-production-6748.up.railway.app@ssh.railway.com
```

Inspect only required public settings/aggregate counts. Variable lists can print secrets. Do not dump settings/customer records/OAuth callback codes to logs/chat. Local manage.py under railway run may write to real production; not for routine tests.

## Backups, scaling and launch

- Initial import finished; never rerun old fixtures against populated production.
- Local migration backups are not ongoing backups of new cloud changes.
- Automatic cloud Postgres/photo backups, independent offsite copies and restore drill are unfinished.
- backup_store supports SQLite only. Old Windows task backs up the old device, not Railway.
- Keep one app replica with attached media volume; use shared object storage before multi-replica scaling.
- Do not recreate/empty DB/volumes on releases or store uploaded photos under ephemeral /app/media or Git.
- Finish domain/Google tests, SMTP if offered, missing business/privacy/delivery disclosures, and real final-domain customer/admin/WhatsApp checks. See HANDOFF.md for the ordered checklist.
