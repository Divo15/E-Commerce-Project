# Shali Collections — complete handoff

**Last verified: 23 October 2026, Asia/Calcutta.** This is the main continuation record for a new device/chat. It supersedes older summaries and historical setup notes where they conflict.

## 1. Read first / resume prompt

The original store is ALREADY running on Railway. Its accounts, catalogue, carts, posters and uploaded photos were migrated and verified. Do not recreate the project, repeat the initial import, replace the live database, reset passwords or redesign the homepage to recover it.

The current task is completing the GoDaddy domain and remaining launch checks. The client owns the GoDaddy login and will make DNS changes herself; she is not sharing her account. Friendly, compact instructions have been provided. Her DNS changes are still pending at the last check.

- Repository: https://github.com/Divo15/E-Commerce-Project
- Working/deployed branch: **testing**. The main branch is older.
- Working cloud site: https://e-commerce-project-production-6748.up.railway.app/
- Cloud admin: https://e-commerce-project-production-6748.up.railway.app/admin/
- Intended canonical address: **https://www.shalicollections.com/**.
- Bare domain shalicollections.com will forward to www through GoDaddy.
- New computer: [CONTINUATION_GUIDE.md](CONTINUATION_GUIDE.md).
- Railway operations: [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md).
- Ready-to-forward client instructions: [CLIENT_DOMAIN_SETUP.md](CLIENT_DOMAIN_SETUP.md).

Paste into a new chat:

> Continue Shali Collections from HANDOFF.md, CONTINUATION_GUIDE.md and RAILWAY_DEPLOYMENT.md on testing. The original store is migrated to Railway PostgreSQL and persistent /data/media. Do not repeat the initial import or restore old SQLite over production. The client must save the GoDaddy www CNAME and ownership TXT; this was still pending. Finish domain verification/forwarding, Google callbacks/canonical origin, automated cloud/offsite backups and final customer-flow checks. Preserve the existing design and data. Keep secrets and customer exports out of Git/chat.

## 2. Verified live state

| Check | Result on 23 October 2026 |
|---|---|
| Web service and Postgres | Both running successfully |
| Latest app code commit | d459ca0 |
| App database engine | django.db.backends.postgresql |
| Database service image | PostgreSQL 18 Railway template |
| Production DEBUG | false |
| Persistent app mount | /data |
| MEDIA_ROOT | /data/media |
| Idle sleeping | Disabled for both inspected service deployments |
| Homepage, login, admin login, returns/refunds | HTTP 200 |
| CSS and hero JavaScript | HTTP 200 |
| Original hero | Three slides present |
| Referenced photos | All 28 unique referenced images returned 200 and matching checksums |
| Restart durability | Original records and 37 uploaded files survived app restart |
| www DNS/ownership | NOT verified yet |
| www certificate | Validating ownership; not ready |

Latest full regression suite: **169 tests passed**. After the final HTTPS-setting adjustment, the focused **28 media/homepage/WhatsApp tests passed**. No customer password was used for these checks. Page/asset checks do not prove real Google consent, SMTP delivery or WhatsApp sending works on the final domain.

### Live baseline counts

| Data | Count |
|---|---:|
| Accounts | 3 |
| Departments / categories / subcategories | 4 / 8 / 10 |
| Saved hero posters | 5 |
| Products / inventory rows | 8 / 10 |
| Saved carts / cart items | 3 / 4 |
| Order drafts / order items | 0 / 0 |
| Uploaded files | 37 |

Five posters are saved, but only the **three newest nonempty records** appear. Counts will change as the owner/customers use the site; never force production back to these baseline counts.

## 3. Code, storage and source of truth

| Item | Location |
|---|---|
| Code and Markdown | GitHub testing branch |
| Live accounts, products, prices, inventory, carts, poster records | Railway Postgres |
| Live uploaded photos | App persistent volume /data/media |
| CSS, JS, logo, fallback campaign image | ecommerce/static/shali in Git; collected to /app/static |
| Production secrets | Railway web-service variables, never Git |
| Old active LOCAL database | D:/ShaliData/db.sqlite3 |
| Old active LOCAL uploads | D:/ShaliData/media |
| Old-device verified backups | D:/ShaliBackups |

Cloud-admin additions save details in PostgreSQL and photos in /data/media. They survive app restarts/deployments while the resources are provisioned. A volume is not a backup or a guarantee against deletion/cancellation/nonpayment.

Local-admin changes save on that computer and do not synchronize with Railway. Since migration, production is authoritative for new live changes. A clone contains code, not the live database, uploaded photos or secrets. The live site does not require the old computer/ngrok to remain running.

## 4. Railway resource IDs

| Resource | Value |
|---|---|
| Project name | carefree-optimism |
| Project ID | 890fe855-842e-4f3c-8e53-1d7dcdabf8ac |
| Environment | production |
| Environment ID | 1b9dc4c3-99ee-4377-9f19-c84629e98d0f |
| App service | E-Commerce-Project |
| App service ID | d00702f4-0896-4ad0-b730-8c55a06582a0 |
| Database service | Postgres |
| Database service ID | e15ca43d-1e81-4c00-8654-80036fd99a76 |
| App volume | e-commerce-project-volume |
| App volume ID | 25d8322f-7959-48b9-95a8-3755d15bfc0d |
| App volume mount / allocated capacity | /data / 5000 MB |
| DB volume | postgres-volume |
| DB volume ID | b4d9a201-2c9e-4065-85b6-73d83b73b700 |
| DB volume mount / allocated capacity | /var/lib/postgresql/data / 5000 MB |
| Web target port | 8080 |
| Region observed | US East (iad); not changed during this work |

Dashboard: https://railway.com/project/890fe855-842e-4f3c-8e53-1d7dcdabf8ac

Use this existing project. Keep **one app replica** while photos use its attached volume. Before horizontal scaling, move images to shared object storage/CDN and plan DB capacity. No microservice rebuild or large server was requested.

Railway Hobby was selected as the initial plan: $5 minimum including $5 usage when discussed; excess usage extra. The $10–20/month initial budget was an estimate, not a guaranteed cap. Verify actual plan, usage and current pricing in Railway. Payment details/tax IDs are managed by the owner; none belong in source control. Render free and Oracle were considered/rejected; no hosting switch is pending.

## 5. Production configuration

Secret values intentionally omitted; these four variables ARE configured privately: DATABASE_URL, DJANGO_SECRET_KEY, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET. Keep the signing key stable across releases.

Public web-service values:

```text
DJANGO_DEBUG=false
DJANGO_DATA_DIR=/data
DJANGO_TRUST_PROXY=true
ACCOUNT_PUBLIC_ORIGIN=https://e-commerce-project-production-6748.up.railway.app
WHATSAPP_ORDER_NUMBER=6583952511
DJANGO_ALLOWED_HOSTS=e-commerce-project-production-6748.up.railway.app,shalicollections.com,www.shalicollections.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://e-commerce-project-production-6748.up.railway.app,https://shalicollections.com,https://www.shalicollections.com
```

On the WEB service, DATABASE_URL references:

```text
${{Postgres.DATABASE_URL}}
```

Do not put that self-reference on Postgres itself; it keeps its generated connection URL. ecommerce/database_config.py selects PostgreSQL when DATABASE_URL is set, otherwise SQLite. Invalid/non-PostgreSQL URLs are rejected. Production additionally requires an absolute DJANGO_DATA_DIR because images are stored separately.

Current railway.json startup:

```sh
python manage.py collectstatic --noinput && python manage.py migrate --noinput && gunicorn ecommerce.wsgi:application --bind 0.0.0.0:$PORT
```

WhiteNoise serves static assets. ecommerce/media_views.py serves only image paths referenced by Product, Category or HeroPoster; rejects traversal, unreferenced/private files and nonimage extensions. It uses the persistent media directory even with DEBUG=false.

Production has secure session/CSRF cookies, HTTPS redirects, trusted-proxy HTTPS detection and one-hour HSTS. Subdomain HSTS/preload were not enabled. The app does not automatically source .env files. Use process variables or Railway settings.

**Upcoming deadline:** Railway docs say railway.json/railway.toml Config as Code is deprecated and stops being read on **1 December 2026**. The existing legacy service still uses it. Migrate the existing resources carefully to Railway IaC before then; review the plan and preserve secrets/volumes. NOT done yet. Source: https://docs.railway.com/infrastructure-as-code

## 6. Domain — exact unfinished work

The domain is already bought from GoDaddy. The client will edit her own DNS without sharing her login. The selected plan is **www plus bare-domain forwarding**, not Cloudflare nameserver migration or purchasing another domain.

Railway domains, all target port 8080:

- e-commerce-project-production-6748.up.railway.app: working fallback.
- shalicollections.com: added by user, root setup not yet usable through GoDaddy root CNAME.
- www.shalicollections.com: added by assistant; app allowed-hosts and CSRF settings already include it.

At last inspection www still had CNAME pointing to shalicollections.com, ownership verified=false and certificate validating ownership. Domain syncStatus ACTIVE does not mean DNS ownership/TLS is verified.

### Client DNS records

GoDaddy > My Products > shalicollections.com > Manage DNS > DNS Records.

Edit the EXISTING www CNAME (avoid duplicates):

```text
Type: CNAME
Name: www
Value: xyebi7xd.up.railway.app
TTL: default
```

Add:

```text
Type: TXT
Name: _railway-verify.www
Value: railway-verify=ff1b8e7aaca0d129db38e493044938f37d96cfa6b72cb068dc6d76c0a4e79d36
TTL: default
```

The TXT value is a public domain-ownership token, not an OAuth/DB secret. These values belong to the existing www registration. If that registration is deleted/recreated, re-read current records instead of reusing stale values.

Preserve unrelated DNS records, including MX/SPF/DKIM/DMARC mail configuration. Do not change nameservers or use root CNAME @ in GoDaddy for this plan. The client wanted a friendly message compact enough for one screenshot; offer help on screenshots rather than demanding account access.

### Next steps after her confirmation

1. Check www CNAME, ownership TXT and Railway certificate status. Wait for DNS propagation rather than repeatedly recreating domains.
2. Confirm https://www.shalicollections.com loads the real store and photos with a valid certificate.
3. In GoDaddy DNS > Forwarding, forward bare shalicollections.com to https://www.shalicollections.com, **Permanent (301)**, **Forward only/no masking**.
4. Keep www CNAME pointing to xyebi7xd.up.railway.app. Do not replace it with @ while setting forwarding; that can cause a loop.
5. Verify Google callbacks (next section), then update ACCOUNT_PUBLIC_ORIGIN to https://www.shalicollections.com and deploy once.
6. Test login and buying entirely on the canonical www address. Railway/ngrok/www do not share cookies/sessions.

References: https://www.godaddy.com/en-ca/help/forward-my-godaddy-domain-12123 and https://docs.railway.com/networking/domains/working-with-domains

## 7. Migration — completed, do not rerun blindly

The initial Railway code deployment had an empty temporary SQLite DB, so it showed a fallback campaign and no products. Original data was still on the old computer. Restoring it required data migration, not a new UI.

Completed process:

1. Installed Gunicorn/WhiteNoise, then PostgreSQL URL parsing and Psycopg.
2. Connected Postgres; verified cloud app had zero accounts/catalogue before import.
3. Created a verified SQLite-plus-media backup, exported a consistent snapshot retaining IDs, password hashes and admin flags.
4. Uploaded private transfer archive over SSH/SFTP to the app's persistent /data volume.
5. Enabled production mode, persistent path, existing Google credentials and guarded image serving.
6. Imported records into empty PostgreSQL in one transaction. Guard refused populated tables.
7. Compared every imported record to the fixture and SHA-256 of all 37 images; all identical.
8. Removed remote temporary archive/staging after success; checked public pages/images, restarted app and confirmed persistence.

Private OLD-DEVICE material:

```text
D:/Backend/.local/cloud-transfer-1e091c2ca4/
D:/Backend/.local/cloud-transfer-current.json
D:/ShaliBackups/shali-20261022T201810-74561719.zip
```

Migration directory contains the fixture, SQLite snapshot, image copies, hashes, archive and guarded import script. It contains customer data/password hashes. Never put it in Git, public attachments or /media/. The pointer's remote archive path is historical; the successful import removed that remote file.

Production now contains records. Any further migration needs a fresh backup/reconciliation plan; never delete cloud rows to re-import this old fixture.

## 8. Accounts, admin and Google sign-in

Admin business account: rajani.cherian@gmail.com. No password is written here. Custom Account flags are is_admin, is_staff and **is_superadmin**; there is no standard is_superuser field. Normal customers cannot enter admin.

Tabs on the same domain share session cookies. Use separate browser profiles/incognito for simultaneous admin/customer testing. Earlier admin password failures were not proven to be code defects; the user believed the password was mistyped. An isolated test script was removed and the prior admin password hash restored before migration. Do not reset passwords or promote a customer because of a guessed issue.

Google signup/sign-in is preferred. Customers do not choose usernames; an internal ID is generated. Google supplies verified email/name. Missing phone, city, PIN and name details are collected before buying. Account carts survive logout, cookie/session changes and another device; guest carts merge once on sign-in. Product/size rows remain separate and stock is checked. Sign-out is POST/CSRF protected.

### Google credentials exist; final-domain verification is pending

- Google project ID: **shaalicollections** (different spelling from domain).
- Existing client ID/secret are private Railway variables. Old local fallback is D:/Backend/.local/google-oauth.json, excluded from Git.
- Original downloaded JSON lists root and ngrok callbacks:
  - https://shalicollections.com/accounts/google/callback/
  - https://diagnosis-catalyst-skydiver.ngrok-free.dev/accounts/google/callback/
- This downloaded file is historical; it does not reveal Google's current live console settings.
- Add/verify these exact URIs in Google Auth Platform > Clients > EXISTING Web application client:

```text
https://www.shalicollections.com/accounts/google/callback/
https://e-commerce-project-production-6748.up.railway.app/accounts/google/callback/
```

Match HTTPS and trailing slash exactly. Do not create a replacement client just for a domain change. Review Google audience/test users/publishing before inviting all customers.

ACCOUNT_PUBLIC_ORIGIN currently generates Railway-origin links/callbacks. After DNS and Google setup, change it to the canonical www address and deploy. Begin and finish login on the same origin, not cookies from one host and callbacks to another.

Real local/ngrok Google login previously worked. Official token verification with a bounded 30-second clock tolerance fixed an earlier failure. PKCE, state, nonce, signature, audience, issuer, expiry and verified-email checks remain. No Google passwords or access/refresh/ID tokens are stored in customer records. Do not weaken those checks.

### Email/password routes remain, but real email is NOT configured

Local DEBUG defaults to file email under .local/emails, not inbox delivery. Production defaults to SMTP, but a real working mail provider/sender has not been configured/verified. Email signup waits for verification; resend/reset routes cannot be advertised as fully working until email delivery is configured. Google-only users need no site verification email or store password. Existing active email/password accounts remain available.

See ACCOUNT_LIFECYCLE.md, GOOGLE_SIGNIN_SETUP.md and SAVED_CARTS.md for implementation details, reading this handoff first for current deployment state.

## 9. Purchase flow: WhatsApp

The user explicitly chose WhatsApp because no delivery network is ready. Do not add Stripe checkout/delivery integrations without a new request.

- Order recipient: **+65 8395 2511**; WHATSAPP_ORDER_NUMBER=6583952511.
- Old +91 6282069689 was replaced. Do not reintroduce it.
- Cart CTA: **Proceed to WhatsApp to buy**, with WhatsApp logo.
- Buying requires sign-in and complete saved contact details; validates selected size, quantity and stock server-side.
- Message contains ALL selected products, size where relevant, quantity, current unit price, subtotal/total, product URLs and each main-product-photo URL.
- Customer details are full name, email, phone, city and PIN, read from the authenticated account. Submitted price/contact spoofing is ignored.
- Customer reviews the prefilled draft and presses Send. The app never sends the WhatsApp message automatically.
- Photo links are included, not image attachments. WhatsApp controls previews; a preview for every product is not guaranteed.
- Opening WhatsApp does NOT charge payment, confirm an order, reserve stock, deduct stock or clear the cart. Availability/delivery/payment are agreed in chat.
- Product-page Open Graph metadata identifies the product's own photo/title, not the brand logo.
- Legacy shipping/order-draft code is preserved for future work but is not the main public purchase journey.

See WHATSAPP_ORDERS.md. Do not send real test messages to the owner without explicit authorization.

## 10. Design decisions to preserve

- Burgundy/gold branding and existing logo; Prata display font, Manrope body font.
- Burgundy headers on registration/product/account pages; mobile bottom navigation retained.
- Homepage uses newest 3 nonempty HeroPoster records, newest first, switching every **2 seconds** with a fade.
- Dots only: no visible pause icon/pill; CTA has no arrow or separate colored box. It reads Explore collections in Prata over a lower-image gradient on mobile.
- One poster is static/no controls; zero posters shows bundled hero-campaign.webp.
- Autoplay pauses offscreen, on hidden tabs, hover and focus; reduced-motion users select manually.
- Editing a poster doesn't make it newest; ordering follows creation/primary key.
- The fallback saree campaign previously visible on Railway was caused by missing poster data, not a redesign.
- Larger prominent Continue shopping on Account, WhatsApp icon/copy and product-photo sharing metadata were completed.

See HOMEPAGE.md and storefront CSS/templates. Preserve this established design unless the user requests a change.

## 11. Published returns/refunds policy

URL: /returns-refunds/, linked in homepage and shared-storefront footers. Source: ecommerce/templates/policies/returns_refunds.html and ecommerce/static/shali/policies.css. Effective 22 October 2026.

Agreed terms already implemented:

- Shali Collections; Rajani Cherian, Owner.
- Support: rajani.cherian@gmail.com and WhatsApp +65 8395 2511.
- India and Singapore orders.
- Return request within **14 days after delivery**.
- Damaged/defective/incorrect/misdescribed goods and unused change-of-mind returns covered.
- Shali pays approved return shipping, including change-of-mind returns.
- Pierced earrings/customised pieces excluded from change-of-mind only; faulty-goods statutory rights preserved.
- Refund initiation **5–7 business days** after receipt/inspection, or approval if no return required. Bank processing may add time.
- Original payment method where possible; alternative by agreement; no mandatory unboxing video.
- Complaint acknowledgement 48 hours and resolution one month as stated in policy.
- Contact Rajani before returning; she confirms address. Sender address is on package.

The owner did NOT supply the full physical business address. Do not invent it or claim public business information is complete. Business-address/privacy/delivery/contact disclosures need a final review. This is a record of owner decisions, not a new legal audit.

## 12. Backups and private files before replacing the device

Persistent storage is implemented. **Automatic Railway/PostgreSQL backup schedules, independent offsite cloud backups and a cloud restore drill are NOT configured/verified.** Local migration backups are not ongoing cloud backups.

Old Windows computer:

- Active development data: D:/ShaliData/db.sqlite3 and D:/ShaliData/media.
- D:/Backend/db.sqlite3 and D:/Backend/media are older pre-move copies, not the active local data.
- Verified archives: D:/ShaliBackups. Latest migration snapshot: shali-20261022T201810-74561719.zip. UTC filename corresponds to 23 October in India.
- Windows task **Shali Store Backup** runs at 03:00 local time and logon; the old machine must be running/owner signed in. It backs up LOCAL SQLite/media, not Railway/PostgreSQL.
- maintenance commands: backup_store, verify_store_backup, restore_store_backup, configure_store_storage.
- backup_store rejects PostgreSQL. Do not use it as a production Postgres backup.
- SQLite restore tools target a NEW empty directory and verify hashes/integrity; never overwrite live production.

Before wiping the old machine, privately preserve any needed D:/ShaliData, D:/ShaliBackups and D:/Backend/.local, ideally encrypted. .local includes OAuth config, local signing key, local emails and customer migration exports. These must not go to GitHub or public attachments. Recreate env, not copy it as deployment data.

Cloud credentials are already in Railway; the live store does not need the old computer to run. Ensure GitHub/Railway/Google account access and 2FA/recovery methods work on the new device. CLI sessions and SSH private keys are not in Git; recreate/authenticate them or transfer privately. Prefer a new device key over sharing private keys.

Old local backups may be stale relative to changes made in cloud admin since migration. Production is the source of truth. Configure fresh cloud backups before considering the old device disposable as a recovery source.

## 13. New-device development / operational lessons

Full steps: CONTINUATION_GUIDE.md. Clone testing, create a new Python venv, install requirements, and use a LOCAL absolute data directory with no production DATABASE_URL for ordinary tests.

Old development runtime: Python 3.12.13 / Django 6.1 at D:/Backend. Last inspected Railway Python: 3.13.16. Gunicorn runs in Linux/Railway; on Windows use Django runserver. New device paths can differ.

Safe local setup explicitly clears DATABASE_URL and ACCOUNT_PUBLIC_ORIGIN. Otherwise ORM writes or generated links can target production. The app doesn't source .env automatically. A clone's empty local database is expected until private development data is restored.

Railway CLI used: @railway/cli@5.71.0 via npx.cmd. Authenticate on the new machine, then link EXISTING project:

```powershell
npx.cmd --yes @railway/cli@5.71.0 login
npx.cmd --yes @railway/cli@5.71.0 link --project 890fe855-842e-4f3c-8e53-1d7dcdabf8ac --environment production --service E-Commerce-Project
npx.cmd --yes @railway/cli@5.71.0 domain status www.shalicollections.com --service E-Commerce-Project --json
```

railway variable list --json/--kv prints secret values. Keep it private; report only selected public settings or presence booleans. Do not run routine tests/migrations under railway run with production variables.

### Private access

An old-device public key named shali-store-migration is registered. Private key is in that device's user .ssh directory, never Git. Create/register a new device key without overwriting existing keys.

Direct OpenSSH worked after one CLI auto-selected UUID target hung:

```sh
ssh -o BatchMode=yes -o ConnectTimeout=10 e-commerce-project-production-6748.up.railway.app@ssh.railway.com
```

Native SCP/SFTP through that domain also worked. Automatic approval review rejected opening a public Postgres TCP proxy; migration succeeded privately over SSH without it. No public database proxy was created by this work. Do not bypass the rejection or publish DB credentials to retry migration.

## 14. Troubleshooting and Git history

| Symptom | Cause/fix |
|---|---|
| gunicorn: command not found | Added Gunicorn dependency |
| Early logs only had old migrations | Wrong/older branch; testing is current |
| Queued builds/project-creation rate errors | Railway outage/repeated clicks; avoid duplicate deploys |
| vxeycpla.up.railway.app returned Application not found | Not the assigned public service URL |
| Correct domain returned DisallowedHost | Added exact allowed host and deployed variables |
| Plain HTML/giant icons/broken logo | CSS/JS 404; added WhiteNoise/collectstatic |
| Default hero/no products | Empty cloud DB; migrated original records/images |
| Initial migrations repeated after releases | Ephemeral SQLite; switched to Postgres |
| Photos unavailable with DEBUG=false | Added guarded persistent-media image view |
| No verification email | Local file email sink, real provider still missing |
| New tab knows customer | Same-origin session cookies shared across tabs |
| Google token used too early | Official verification now allows 30-second clock skew |

| Commit on testing | Work |
|---|---|
| 0944982 | Account lifecycle, carts, WhatsApp, backups, storefront |
| 429a7d8 | Singapore WhatsApp recipient and hero typography |
| 2d767bf | Gunicorn for Railway |
| 48a683a | WhiteNoise and Railway static startup |
| a3ae5bd | PostgreSQL support/tests |
| d459ca0 | Persistent images, production HTTPS, media tests |

The documentation handoff is committed after these. Use git log/status and the actual GitHub testing head to verify state; do not assume main is current. No private data/media/environment should be staged.

## 15. Ordered remaining work

- [ ] Client saves www CNAME/TXT; verify ownership and HTTPS certificate.
- [ ] Bare-domain forwarding works over HTTPS, no masking/loop.
- [ ] Existing Google client has exact www and Railway callbacks; audience/test users/publishing checked.
- [ ] Set ACCOUNT_PUBLIC_ORIGIN to canonical www after the above and redeploy.
- [ ] Real Google signup/login, profile completion, logout/return login tested on final address.
- [ ] Saved carts persist on another device; stock/size rules and all-item WhatsApp draft tested with consenting test data.
- [ ] Owner confirms correct WhatsApp recipient; customer must manually send draft.
- [ ] SMTP verification/reset sender configured if email/password alternative stays customer-facing, or explicit Google-only UX decision made.
- [ ] Automated cloud DB/photo backups, independent offsite copies and safe restore drill completed.
- [ ] Physical business address and privacy/delivery/contact disclosures completed.
- [ ] Mobile/desktop/admin uploads and secure cookies checked on final domain.
- [ ] Migrate deprecated Railway config before 1 December 2026, preserving existing resources/secrets.

## 16. Collaboration preferences and scope

The user wants the original store preserved and plain explanations of where live data goes. Prefer one concrete next step at a time; act on authorization without repetitive confirmation. Do not ask for passwords or reset/promote accounts based on guesses.

The client is not technical, owns GoDaddy, and does not want to share login. Keep her instructions compact, friendly, screenshot-friendly and limited to the DNS task.

The user was frustrated when local backup folders/tasks were discussed as if they were cloud deployment. Clearly distinguish local tooling from live cloud resources. Do not restart host comparisons or create more local infrastructure unnecessarily.

This device-switch request is to preserve context in Markdown and push it. GitHub preserves code and these notes; it does not automatically preserve raw chat history, ignored private files, databases, media uploads or CLI sessions. Private old-device files need a separate secure transfer if wanted.

## 17. Code map for the next developer

| Location | Responsibility |
|---|---|
| ecommerce/settings.py | Environment, storage, database, email, Google, security and static configuration |
| ecommerce/database_config.py | Validated Railway Postgres URL or local SQLite fallback |
| ecommerce/storage_config.py | Absolute data/backup directories; local override file only in DEBUG |
| ecommerce/urls.py, views.py | Root routes, home/category content queries |
| ecommerce/media_views.py | Production referenced-image streaming |
| ecommerce/templates/base.html, includes/ | Shared shell, header/footer, icons, mobile navigation |
| ecommerce/templates/home.html | Homepage, slideshow markup, custom footer |
| ecommerce/static/shali/ | Brand/static assets; storefront, landing, account and policy CSS/JS |
| category/models.py, admin.py, context_processor.py | Department/category/subcategory, hero posters, menus and admin |
| store/models.py, views.py | Product/inventory, catalogue/search/detail and sharing metadata |
| store/templates/store/product_detail.html | Live product detail |
| ecommerce/templates/store/store.html | Live catalogue/search |
| carts/models.py, services.py, views.py, forms.py | Saved/guest carts, merge, quantity/stock validation and POST actions |
| carts/templates/carts/cart.html | Bag and WhatsApp buying summary |
| accounts/google_auth.py | OAuth start/callback, verification, linking and completion |
| accounts/forms.py, views.py, lifecycle.py | Registration/contact/login, email/password lifecycle and request limits |
| orders/whatsapp.py | Server-generated product/bag WhatsApp drafts and public photo links |
| ecommerce/public_urls.py | Canonical public origin and absolute media/product URLs |
| orders/models.py, views.py, templates/ | Retained legacy unpaid shipping/order drafts, not confirmed purchases |
| maintenance/backups.py and management/commands/ | Local SQLite/media backup, integrity checks and safe restore |

Public route families: /, /categories/, /store/, /store/search/, /store/product/<department>/<category>/<slug>/, /carts/, /checkout/, /accounts/, /admin/, /returns-refunds/, /media/<image-path>. Google routes are /accounts/google/start/ and /accounts/google/callback/. Check each app urls.py for exact mutation endpoints before editing.

Important model rules: product subcategories must belong to the product's category; public listings need a department path; stock is per ProductInventory size; cart rows are unique per cart/product/size; each account owns one saved Cart. Prices/contact information are read on the server. Images are uploaded through admin, not seeded by source migrations. Catalogue cards/search use pagination.

Older standalone React/CDN templates/app.js are visual references, not a separate live frontend to deploy. Django serves this whole storefront; no separate frontend host has been configured or requested.

Additional route/model/delivery-planning history remains in Git: `git show d459ca0:CONTINUATION_GUIDE.md`. That old guide's uncommitted-work, immediate Stripe/Shiprocket priorities and local-storage assumptions were superseded by this handoff and the WhatsApp launch decision.
