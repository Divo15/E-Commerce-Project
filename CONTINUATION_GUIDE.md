# Shaali backend continuation guide

**Prepared:** 2026-10-20

**Repository:** `D:\Backend`

**Branch:** `testing`
**Purpose:** This is the handoff document for continuing the project on another laptop without losing the current work or misunderstanding what has already been built.

---

## 1. Read this before moving machines

The repository has **important uncommitted work**. A normal clone of the `testing`
branch on another laptop will **not** include it.

At the time this guide was written, `git status --short` showed modified documentation,
templates, views, and tests, plus new stylesheet/template files. This work must be
preserved before changing laptops.

### Safest transfer options

Choose one of these options before leaving this laptop:

1. **Recommended: make a WIP commit on `testing`.** Review the changes, then commit
   them and push the branch to the remote. Do not include `db.sqlite3`, `media/`,
   `store/media/`, `env/`, `.env`, or credentials.
2. **If a commit is not wanted:** copy the complete `D:\Backend` directory to the new
   laptop, including the hidden `.git` directory and untracked files. The local SQLite
   database and uploads are also needed if the same local catalogue must appear.
3. **Patch alternative:** create a Git patch for tracked changes and separately copy all
   untracked files. This is more error-prone, so use it only if the first two options
   are unsuitable.

On the new laptop, immediately run:

```powershell
cd D:\Backend
git status --short
git branch --show-current
```

The branch must be `testing`, and the expected work-in-progress files should still be
present. Do not run `git reset --hard`, `git clean`, or discard changes unless you have
confirmed they are backed up.

### Local-only data that is not stored in Git

- `db.sqlite3`: the current local catalogue, admin data, and development state.
- `media/`: the configured Django upload directory.
- `store/media/`: old/original upload location retained during recovery.
- `env/`: the local Python virtual environment; recreate it on a new computer rather
  than committing or copying it unless necessary.
- Any Stripe, Shiprocket, email, database, or deployment credentials.

The project is configured with `MEDIA_ROOT = BASE_DIR / 'media'`. If you want the
current images on the new laptop, transfer `media/` privately. Do not commit media or
database files just to move them between computers.

---

## 2. Product summary and completion level

Shaali is a Django e-commerce storefront for Indian ethnic fashion and jewellery.

### Current estimate

- **About 65% complete overall.**
- **80–85% of the browsing/storefront experience** is implemented.
- **About 0–20% of the payment-to-delivery lifecycle** is implemented. A shipping
  address can create an unpaid draft order, but payment, courier fulfillment, and
  confirmed-order completion do not yet exist.
- **Production readiness is not complete.** The settings are development-oriented.

### Already implemented

- Admin-managed departments, categories, subcategories, hero posters, products,
  images, and size-specific inventory.
- Public homepage, category navigation, department/category/subcategory filtering,
  search, pagination, product detail, and responsive templates.
- Product sizes and stock-aware add-to-bag forms.
- Session-based cart with separate rows per product/size, quantity changes/removal,
  CSRF protection, stock validation, and a live bag count.
- Custom email-based account registration, login, logout, safe local return URLs, and
  guest-cart preservation after login.
- Shipping-address form that creates/updates an unpaid order draft and snapshots its
  cart items.
- Read-only Django Admin order details for drafts.

### Not implemented

- Stripe Checkout session creation and payment-success handling.
- Stripe webhook verification and idempotent confirmed-order completion.
- Atomic inventory deduction after a confirmed payment.
- Shipping serviceability, shipping rates, tax calculation, courier selection, labels,
  shipment tracking, Shiprocket integration, or delivery webhooks.
- Customer order-history/tracking pages.
- Transactional customer/admin order emails.
- Material/fabric, occasion, and sale-price catalogue fields.
- Production configuration, production database/storage, deployment, monitoring, and
  background-job/retry infrastructure.

---

## 3. Technology and local setup

| Area | Current choice |
| --- | --- |
| Language | Python 3.12.13 locally |
| Framework | Django 6.1 |
| Database | SQLite (`db.sqlite3`) for development |
| Image support | Pillow |
| Payments dependency | `stripe==15.6.1` is installed but not wired into views |
| Templates | Django templates; no active frontend SPA build |
| Styling | Project static CSS/JavaScript under `ecommerce/static/shali/` |
| Email in development | Django console backend |

### Create a new local environment

```powershell
cd D:\Backend
py -3.12 -m venv env
.\env\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

For the existing environment, use:

```powershell
D:\Backend\env\Scripts\python.exe manage.py runserver
```

Open `http://127.0.0.1:8000/` for the storefront and
`http://127.0.0.1:8000/admin/` for Django Admin.

### Baseline verification commands

Run these after transferring the project and after backend changes:

```powershell
cd D:\Backend
.\env\Scripts\python.exe manage.py check
.\env\Scripts\python.exe manage.py makemigrations --check --dry-run
.\env\Scripts\python.exe manage.py migrate --check
.\env\Scripts\python.exe manage.py test --verbosity 1
git -c safe.directory=D:/Backend diff --check
```

The existing documentation reports that all 90 tests passed on 2026-10-15. The
catalog/landing-page work listed in section 9 is currently uncommitted, so rerun the
suite after transferring it rather than treating that historical result as a current
verification.

If Git reports "dubious ownership" in a sandboxed terminal, do not alter repository
files. Use the one-command configuration form already used in this workspace:

```powershell
git -C D:\Backend -c safe.directory=D:/Backend status --short
```

---

## 4. Repository map

```text
D:\Backend\
├── accounts/              Custom email-based user model, forms, authentication views
├── carts/                 Session cart models, forms, stock service, views, tests
├── category/              Department/category/subcategory/hero models and admin
├── ecommerce/             Project settings, root URLs, shared templates/static files
├── orders/                Shipping form, unpaid draft order models, order snapshots
├── store/                 Product/inventory models, catalogue/search/detail views
├── media/                 Active local upload root (ignored by Git)
├── static/                `collectstatic` output, if generated (ignored by Git)
├── db.sqlite3             Local development database (ignored by Git)
├── manage.py
├── requirements.txt
├── README.md
├── HANDOFF.md
└── CONTINUATION_GUIDE.md  This document
```

Important project documentation already present:

- `README.md`: high-level feature/status document.
- `HANDOFF.md`: prior implementation handoff and next tasks.
- `RECOVERY_REVIEW.md`: recovery carried out on 2026-10-15 after an interrupted work
  session, including database/media recovery information.
- `CATALOG_IMPLEMENTATION.md`: current uncommitted catalog/cart UI documentation.
- `CART_IMPLEMENTATION.md`, `SHIPPING_IMPLEMENTATION.md`, `HOMEPAGE.md`, and
  `PRODUCT.md`: detailed functional and brand notes.

No `AGENTS.md` file was found in this repository when this guide was prepared.

---

## 5. Configuration and security boundaries

`ecommerce/settings.py` currently contains development settings:

- SQLite database at `BASE_DIR / 'db.sqlite3'`.
- Static source directory: `ecommerce/static/`.
- Media root: `media/`, served by Django only in development.
- Console email backend.
- Custom user model: `accounts.Account`.
- `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET` are read from environment variables
  and default to empty strings.
- `DJANGO_DEBUG`, `DJANGO_SECRET_KEY`, and `DJANGO_ALLOWED_HOSTS` configure deployment.
  Production startup requires a private key and allowed hosts; local debug mode uses a temporary secret if none is supplied.

### Rules for future work

- Never put API secrets, passwords, webhook secrets, or production keys in Git,
  templates, JavaScript, tests, screenshots, or this file.
- Use environment variables or a private deployment secret manager for Stripe,
  Shiprocket, email, database, storage, `SECRET_KEY`, `DEBUG`, and allowed hosts.
- Do not expose payment or Shiprocket credentials to the browser.
- Do not trust totals, stock, address data, payment-success redirects, or delivery
  status values that arrive from a browser. Revalidate on the server.

---

## 6. Application architecture and routes

### Root routing

`ecommerce/urls.py` includes:

| URL prefix | App / purpose |
| --- | --- |
| `/` | Homepage |
| `/admin/` | Django Admin |
| `/accounts/` | Account routes |
| `/categories/` | Category directory |
| `/store/` | Catalogue, product detail, search |
| `/carts/` | Session cart |
| `/checkout/` | Shipping draft flow |

### Account routes

| URL | Name | Notes |
| --- | --- | --- |
| `/accounts/register/` | `accounts:register` | Creates/activates custom email user |
| `/accounts/login/` | `accounts:login` | Preserves guest cart during session rotation |
| `/accounts/logout/` | `accounts:logout` | POST-only |

`accounts.Account` is the configured user model. Email is the login identifier.
It extends `AbstractBaseUser`; registration lowercases/normalizes emails and stores a
hashed password. Keep this user model in place—changing the configured user model in
an existing Django project is disruptive.

### Catalogue routes

| URL | Name |
| --- | --- |
| `/store/` | `store:store` |
| `/store/search/?keyword=silk` | `store:search` |
| `/store/category/<department_slug>/` | `store:products_by_department` |
| `/store/category/<department_slug>/<category_slug>/` | `store:products_by_category` |
| `/store/category/<department_slug>/<category_slug>/<subcategory_slug>/` | `store:products_by_subcategory` |
| `/store/product/<department_slug>/<category_slug>/<product_slug>/` | `store:product_detail` |

The public catalogue only includes available products with a complete department path.
Search matches product name/description; blank search returns no results. Catalogue and
search are paginated 12 products at a time. The views prefetch inventory, calculate
valid stocked options, and preserve size validation on the server through cart forms.

### Cart routes

| URL | Name | Method |
| --- | --- | --- |
| `/carts/` | `cart` | GET |
| `/carts/add_cart/<product_id>` | `add_cart` | POST |
| `/carts/items/<item_id>/update/` | `update_cart` | POST |
| `/carts/items/<item_id>/increase/` | `increase_cart` | POST |
| `/carts/items/<item_id>/decrease/` | `decrease_cart` | POST |
| `/carts/items/<item_id>/remove/` | `remove_cart` | POST |

### Current checkout routes

| URL | Name | Meaning |
| --- | --- | --- |
| `/checkout/shipping/` | `orders:shipping_details` | Collect or update delivery address on an unpaid draft |
| `/checkout/shipping/review/` | `orders:shipping_review` | Review the current browser session's saved draft |

There is **no payment URL or completed-order URL yet**.

---

## 7. Data model and existing business rules

### Category hierarchy

`Department → Category → SubCategory` describes navigation.

- `Category.department` is optional in admin but public pages exclude categories and
  products without one.
- `Product.category` is required.
- A product can have multiple subcategories, but the model signal rejects selections
  belonging to another category.
- `HeroPoster` is managed in admin; the newest poster is used on the homepage.

### Products and inventory

`store.Product` holds product name, slug, description, colour, integer rupee price,
three optional image fields, availability, category, subcategories, timestamps, and a
`size_type`.

Allowed size types are:

| Product size type | Inventory size allowed |
| --- | --- |
| `clothing` | `s`, `xl`, `xxl` |
| `free_size` | `free_size` |
| `no_size` | `no_size` |

`ProductInventory` records quantity for each product/size and has a unique
product/size constraint. Its validation prevents a size that is incompatible with the
product's size type. Stock is not reserved on addition to the cart.

### Cart rules

`Cart` belongs to the browser session key, not directly to a user.

- A cart is created only when an item is added; simply browsing does not create one.
- `CartItem` is unique on `(cart, product, size)`.
- Adding the same product/size increases its quantity; a different size is a different
  row.
- Every mutation is POST-only and protected by the normal Django CSRF middleware.
- Cart changes call `carts.services.validate_stock`, which locks and checks the chosen
  inventory record.
- Products can be removed even if they later become unavailable. They cannot be
  increased beyond stock or submitted to shipping with invalid/outdated stock.
- The navigation count is the total number of active units, not the number of rows.

### Current order-draft rules

`orders.Order` is currently a shipping/payment draft, not a completed customer order.

It holds the session cart reference, optional authenticated user, one of
`pending/paid/failed/cancelled`, a snapshot total, contact/address fields, optional
Stripe reference fields, and `paid_at`.

`OrderItem` stores snapshots of product, product name, unit price, quantity, and size.
The current `shipping_details` POST does the following atomically:

1. Fetches the current browser session's active cart.
2. Validates all shipping form fields, including Indian PIN syntax and phone number.
3. Rechecks each row's size-specific stock.
4. Creates or refreshes one eligible pending draft for that cart/session.
5. Replaces its `OrderItem` snapshots and total with the current cart values.
6. Saves the order ID in `request.session['checkout_order_id']`.
7. Redirects to shipping review.

It deliberately does **not** charge, reserve stock, deduct stock, clear the cart,
create a courier shipment, or email anyone.

Drafts are no longer editable by this shipping view when paid or when a Stripe session
or payment-intent reference exists. Another browser session cannot access or overwrite
a session's draft merely by supplying its ID.

---

## 8. Template and static layout

The live shared layout starts at `ecommerce/templates/base.html`; shared includes live
under `ecommerce/templates/includes/`. Main active templates include:

- `ecommerce/templates/home.html`
- `ecommerce/templates/categories.html`
- `ecommerce/templates/store/store.html`
- `store/templates/store/product_detail.html`
- `carts/templates/carts/cart.html`
- `orders/templates/orders/shipping_details.html`
- `orders/templates/orders/shipping_review.html`
- account templates in `accounts/templates/accounts/`

Storefront assets are under `ecommerce/static/shali/`. The old root-level React/CDN
templates and `ecommerce/templates/app.js` are visual references only; do not treat
their hardcoded data as live application behaviour.

---

## 9. Current uncommitted storefront work

This section is especially important when continuing elsewhere. The currently dirty
working tree contains visual/catalog work in addition to documentation changes.

### Modified tracked files

- `CART_IMPLEMENTATION.md`
- `HANDOFF.md`
- `HOMEPAGE.md`
- `PRODUCT.md`
- `README.md`
- `carts/templates/carts/cart.html`
- `carts/tests.py`
- `carts/views.py`
- `ecommerce/templates/PRODUCT.md`
- `ecommerce/templates/home.html`
- `ecommerce/templates/includes/search_form.html`
- `ecommerce/templates/store/store.html`
- `ecommerce/tests.py`
- `store/views.py`

### New, untracked files

- `CATALOG_IMPLEMENTATION.md`
- `ecommerce/static/shali/catalog-cart.css`
- `ecommerce/static/shali/landing.css`
- `ecommerce/static/shali/landing.js`
- `ecommerce/templates/store/includes/product_card.html`

### What those changes do

- Convert the homepage into the current Shali landing-page presentation, with hero,
  category/collection sections, fallback states, and landing-specific CSS/JavaScript.
- Convert catalogue/search into the shared storefront layout with responsive product
  cards, navigation, breadcrumb, search, pagination, stock states, and reusable card
  partials.
- Improve cart presentation while retaining server-side POST cart operations and stock
  rules.
- Add stock context to paginated catalogue/search product cards in `store/views.py`.
- Avoid duplicate search-input IDs by allowing the shared search include to accept a
  `search_id`.
- Add/adjust tests for these rendering and cart/catalog behaviours.

Before beginning payment or delivery work, preserve these files and run the full test
suite. Keep backend behaviour and template/UI work separate in commits where possible.

---

## 10. What must be built next: payment and confirmed orders

The correct payment boundary is **after** shipping address review and **before** any
courier order creation. Do not consider the browser redirect after payment to be proof
of payment; only Stripe's verified server-to-server webhook is authoritative.

### Suggested Stripe implementation sequence

1. Add a POST-only endpoint on the shipping review page: “Continue to payment.”
2. In one database transaction, load the current eligible pending draft, revalidate
   each product price, availability, size, quantity, and stock, then build the Stripe
   Checkout line items from trusted server-side values.
3. Store the created Stripe Checkout Session ID on the draft before redirecting the
   customer to Stripe. Prevent a second active checkout session for the same draft.
4. Add success/cancel display pages. They are informational only; neither marks an
   order paid.
5. Add a CSRF-exempt Stripe webhook endpoint that verifies Stripe's signature using
   `STRIPE_WEBHOOK_SECRET` and handles the relevant completed-payment event.
6. In a transaction with row locks, make completion idempotent: a repeated event must
   never deduct inventory twice or send duplicate mail.
7. Recheck the order snapshot/prices and lock the relevant inventory rows. If a paid
   order cannot safely be fulfilled because stock was sold elsewhere, route it to a
   defined manual/refund exception flow rather than silently delivering unavailable
   inventory.
8. Mark payment as paid, set `paid_at`, save the payment intent ID, deduct inventory,
   and clear only the relevant cart rows after successful completion.
9. Create an order confirmation record/email and make the confirmed order immutable
   except for fulfillment/shipment fields.

### Important design decision

The present `Order.status` values (`pending`, `paid`, `failed`, `cancelled`) represent
payment state. Delivery state should be a separate field/model, such as
`fulfillment_status` or a dedicated `Shipment`; do not overload payment status with
`shipped` or `delivered`.

---

## 11. Delivery and Shiprocket implementation plan

### In plain language

Stripe confirms “the customer paid.” Shiprocket/courier confirms “the parcel moved”
and later “the parcel was delivered.” These are separate facts and should be stored
separately.

### Desired customer flow

1. Customer adds products and enters a valid shipping address.
2. The site checks whether that PIN code can be served and displays delivery charge,
   estimated delivery date if available, and final total before payment.
3. Customer pays through Stripe.
4. After payment is confirmed by Stripe webhook, the backend creates/submits the
   shipment to Shiprocket (or queues it for a staff member), selects a courier, stores
   Shiprocket shipment ID and AWB/tracking number, and schedules pickup.
5. Shiprocket sends tracking updates to our server.
6. The server records the update and the customer sees the latest delivery state in
   their order/tracking page.

### Information required before a live Shiprocket integration

- A Shiprocket seller account and API access credentials.
- Verified pickup address(es) and business/KYC/tax information in Shiprocket.
- Which orders are handled by Shiprocket: prepaid only, cash-on-delivery, or both.
- Package weight/dimensions for each product or a consistent packing rule. The current
  `Product` model has no weight/dimension fields, so rate calculation cannot be
  reliable without adding them or defining a rule.
- Tax policy, free-shipping threshold, fixed/weight-based rate rules, and whether the
  website displays live courier rates or a single store-owned rate.
- Whether staff create the shipment manually in Shiprocket initially, or the website
  should create it automatically after payment.
- Customer tracking access policy: authenticated “My Orders”, guest email/order-number
  lookup, or both.

### Recommended model shape

Use a separate shipping layer rather than adding many unrelated fields to `Order`.
The exact names are flexible, but the following information is needed:

| Concept | Essential data |
| --- | --- |
| Shipping quote | order, serviceable flag, carrier/service, shipping charge, tax, ETA, quoted timestamp, source |
| Shipment | order, provider, Shiprocket order ID, Shiprocket shipment ID, AWB, courier name, tracking URL, current status, last status time, pickup/dispatch/delivery timestamps |
| Shipment event | shipment, provider event/reference ID if supplied, raw status/code, mapped internal status, event time, raw payload for audit/debugging |

Copy/persist the charged shipping amount and tax onto the confirmed order. Never
recalculate a historical order using today's shipping prices.

### Shiprocket API and status updates

Shiprocket can create/update orders, assign an AWB, schedule pickup, and provide
shipment tracking. It can also send a webhook to a configured public HTTPS callback
whenever a tracking event changes. The webhook is the preferred way to keep the
website current; tracking API polling is useful as a reconciliation fallback.

The webhook handler should:

1. Be reachable by Shiprocket over public HTTPS; localhost will not work in production.
2. Validate a configured webhook security token/header before trusting the payload.
3. Locate the internal shipment using the stored Shiprocket shipment ID and/or AWB.
4. Save the raw payload and map Shiprocket's detailed status to a small internal set,
   for example `created`, `awb_assigned`, `pickup_scheduled`, `picked_up`,
   `in_transit`, `out_for_delivery`, `delivered`, `delivery_failed`, `rto`,
   `cancelled`, `lost_or_damaged`.
5. Be idempotent: the same event may arrive again or out of order; never create
   duplicate shipment records or duplicate customer emails.
6. Return a quick successful response after safely storing the update. Long-running
   email/API work should run through a queue in production.
7. Reconcile periodically through Shiprocket's tracking/shipment endpoints to recover
   from missed webhooks.

Shiprocket's API documentation lists common milestones such as Shipped, In Transit,
Out for Delivery, Delivered, RTO, delayed, damaged, and pickup events. Read its current
documentation during implementation because provider payloads, credentials, and status
codes can change: <https://apidocs.shiprocket.in/>.

### Serviceability and rate implementation order

1. First add local, admin-managed delivery-zone/PIN-code rules and a testable quote
   service. This gives a reliable fallback even if the carrier API is unavailable.
2. Add package data and an order quote snapshot.
3. Add Shiprocket serviceability/rate calls behind a provider service module; use the
   local rules as a graceful failure strategy if that fits the business policy.
4. Add shipment creation only after a Stripe webhook confirms payment.
5. Add Shiprocket webhook reception and customer tracking UI.
6. Add staff controls in Django Admin for shipment exceptions, reattempts, cancellations,
   RTO, and manual status correction with audit notes.

### Email notifications

At minimum, send:

- Customer: payment/order confirmation, shipment created/AWB, dispatched, delivered,
  and material delivery exception notifications.
- Store/admin: new paid order, payment/shipment failure, stock conflict, and delivery
  exception notifications.

Use a real transactional email provider in production. The current console email backend
only prints emails in the server terminal. Email sending must be idempotent and should
not make a successful payment webhook fail if the mail provider is temporarily down.

---

## 12. Deferred catalogue and production work

### Catalogue fields

Add `material`/`fabric`, `occasion`, and sale-price support across:

1. `Product` model and a new migration.
2. Django Admin form/list/filter/search configuration.
3. Product detail, product cards, catalogue/search display, and accessible labels.
4. Server-side pricing rules. Use one clearly defined amount for Stripe Checkout and
   OrderItem snapshots; do not let a client select a sale price.
5. Tests for migration/defaults, display, and checkout snapshots.

### Production checklist

- Move all settings/secrets to environment variables.
- Set `DEBUG=False`, `ALLOWED_HOSTS`, HTTPS/security cookie settings, CSRF trusted
  origins, and secure redirects correctly.
- Replace development SQLite with a backed-up production database (normally PostgreSQL).
- Use durable object storage/CDN for uploaded media and static files.
- Configure a transactional email provider and domain authentication.
- Set up Stripe/Shiprocket webhook URLs, secret validation, logging, monitoring, alerting,
  backups, and error tracking.
- Run migrations through deployment, not manually against unknown production state.
- Add a background worker/queue for retries, email, and provider reconciliation.

---

## 13. Testing strategy

Existing tests cover account flows, catalogue/search/detail behavior, stock rules,
cart mutations/isolation, CSRF, guest-cart preservation, shipping form validation,
order snapshots, and admin access. The documented successful result is 90 tests on
2026-10-15.

### Tests required for upcoming payment/delivery work

- Checkout cannot start from an empty, stale, paid, or another session's draft.
- Checkout uses server-side price/quantity/stock, never values posted by the browser.
- Webhook signature is required; invalid/unknown events change nothing.
- Payment completion is idempotent under duplicate webhooks and concurrent requests.
- Inventory is deducted exactly once and never below zero.
- Failed/cancelled payment never deducts stock or clears the cart.
- Shipping price/tax and quoted serviceability are persisted on the order snapshot.
- Shiprocket creation does not occur before confirmed payment.
- Duplicate/out-of-order Shiprocket webhooks are safely handled.
- Customer can see only their own order/tracking information.
- Email dispatch is queued/idempotent and provider failures do not corrupt order state.

Use mocked Stripe/Shiprocket HTTP responses in automated tests. Do not call real payment
or courier APIs from unit tests.

For browser verification, use a temporary database copy and test desktop plus small
phone widths. Do not create test orders in the local catalogue database.

---

## 14. Recommended implementation order

1. Preserve/commit the current uncommitted landing/catalog/cart work and run the test
   suite after moving laptops.
2. Finish and visually test the current storefront changes before mixing in payments.
3. Decide delivery business rules and obtain Shiprocket account/API details.
4. Add product package data plus shipping quote/shipment/event models and migrations.
5. Build local serviceability/rate quote service, admin setup, and shipping-review UI.
6. Implement Stripe Checkout and verified payment webhook completion.
7. Implement automatic Shiprocket shipment creation after payment confirmation.
8. Implement Shiprocket webhook tracking, customer tracking/order history, and admin
   exception tools.
9. Add transactional emails and retry/reconciliation work.
10. Add catalogue deferred fields, then production configuration/deployment.

Keep migrations, tests, and documentation with the feature that needs them. Make small
commits with one purpose each; this will make it much safer to debug payment and courier
flows later.

---

## 15. Important things not to break

- Preserve the custom `accounts.Account` user model.
- Preserve session-cart ownership checks; never retrieve a cart/order only by public ID
  without verifying user/session ownership.
- Keep cart and checkout mutations POST-only and CSRF-protected.
- Keep stock validation on the server and lock relevant rows during confirmation.
- Preserve `OrderItem` snapshots; historic orders must not change when a product title
  or price changes later.
- Do not let shipping-address posts overwrite a paid/payment-started draft.
- Do not clear carts or deduct inventory on address save, checkout redirect, or browser
  success page—only after verified confirmed payment.
- Keep uploaded media, database files, environments, `.env` files, and credentials out
  of Git.
- Do not discard the uncommitted storefront work listed in section 9.

---

## 16. First-session checklist on the new laptop

1. Confirm the project folder, branch, and uncommitted files transferred correctly.
2. Recreate the Python environment and install `requirements.txt`.
3. Privately copy development `media/` and, only if needed, the development SQLite
   database; otherwise start fresh with migrations and create an admin user.
4. Run the baseline verification commands from section 3.
5. Start the server and check homepage, catalogue, product detail, cart, login,
   shipping form, and shipping review manually.
6. Read `HANDOFF.md`, `CATALOG_IMPLEMENTATION.md`, and this guide before changing
   checkout or delivery code.
7. Create a backup before applying any migration to a valuable SQLite database.

Once these checks pass, the safest next feature is shipping quotes/serviceability,
followed by Stripe payment completion and then Shiprocket fulfillment/tracking.
