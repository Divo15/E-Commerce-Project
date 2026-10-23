# Shali Collections

Django storefront for ethnic clothing/jewellery, with Google sign-in, persistent account carts, admin-managed catalogue and WhatsApp purchase requests.

**Updated 23 October 2026.** The original store is deployed on Railway PostgreSQL with a persistent photo volume. Final GoDaddy domain connection and launch checks are in progress.

## Continue the project

- **[HANDOFF.md](HANDOFF.md)**: full current state, resource IDs, conversation decisions, migration proof, DNS records and unfinished work. Read first in a new chat.
- **[CONTINUATION_GUIDE.md](CONTINUATION_GUIDE.md)**: switch devices, preserve private local files and set up safe development.
- **[RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md)**: live deployment/domain operations.
- **[CLIENT_DOMAIN_SETUP.md](CLIENT_DOMAIN_SETUP.md)**: short GoDaddy instructions for the client.

Repository: https://github.com/Divo15/E-Commerce-Project — use **testing**; main is older.

Live site: https://e-commerce-project-production-6748.up.railway.app/

Cloud admin: https://e-commerce-project-production-6748.up.railway.app/admin/

Intended final URL: https://www.shalicollections.com/ — DNS verification pending at last check.

## Implemented

- Departments/categories/subcategories, products with up to three photos and size-specific inventory.
- Responsive catalogue/search/product pages, shared storefront and Django Admin.
- Newest-three-poster slideshow, two-second interval, dots and reduced-motion support.
- Google OAuth/contact completion, internally generated usernames, legacy email/password lifecycle.
- Account-owned saved carts, guest merging, server-side pricing/stock checks and POST/CSRF protection.
- WhatsApp drafts to +65 8395 2511 with all selected products, product/photo links and saved contact details. Customer reviews and presses Send.
- Published 14-day returns/refunds policy at /returns-refunds/.
- Gunicorn/WhiteNoise, PostgreSQL support, secure production settings and guarded persistent photo serving.
- Verified original-store import and restart durability; latest full regression suite: 169 passed.

WhatsApp does not take payment, confirm orders, reserve/deduct stock or clear the bag. Delivery/payment are agreed in chat. Legacy shipping/order-draft code remains; automated delivery and Stripe completion are not the current main purchase flow.

## Storage and development

| Item | Production location |
|---|---|
| Accounts, products, prices, inventory, carts, poster records | Railway Postgres |
| Uploaded photos | App persistent volume /data/media |
| Static assets | Git, collected/served by WhiteNoise |
| Secrets | Railway variables, never Git |

Local development uses SQLite without DATABASE_URL. Local admin edits do not sync to production. Git does not contain uploads/customer DB/secrets; follow the continuation guide for private development-data recovery.

```powershell
git clone --branch testing https://github.com/Divo15/E-Commerce-Project.git
cd E-Commerce-Project
py -3.12 -m venv env
.\env\Scripts\python.exe -m pip install -r requirements.txt
```

Set local-only variables as documented in CONTINUATION_GUIDE.md before migrations/tests/runserver. Never use production DATABASE_URL for ordinary development.

## Still to finish

Client DNS/HTTPS and bare-domain forwarding; Google final callbacks/canonical origin; cloud/offsite backups and safe restore test; SMTP if email/password verification/reset remain offered; business-address/privacy/delivery disclosures; final-domain account/cart/admin/WhatsApp checks.

Legacy railway.json must be migrated before Railway's documented **1 December 2026** cutoff. See the deployment guide.

## Other documentation

[Homepage](HOMEPAGE.md), [catalogue](CATALOG_IMPLEMENTATION.md), [accounts](ACCOUNT_LIFECYCLE.md), [Google sign-in](GOOGLE_SIGNIN_SETUP.md), [saved carts](SAVED_CARTS.md), [WhatsApp](WHATSAPP_ORDERS.md), [local backup tooling](PERSISTENT_STORAGE.md), [legacy shipping drafts](SHIPPING_IMPLEMENTATION.md).

RECOVERY_REVIEW.md and UI_REVIEW_HANDOFF.md are historical records, not current deployment instructions. Keep database files, uploads, .local, .env, environments, private keys and exports out of Git.
