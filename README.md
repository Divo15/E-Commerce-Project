# Shaali E-commerce

Shaali is a Django storefront for Indian ethnic fashion and jewellery. Customers can browse and search collections, view product images, select stocked sizes, manage a session cart, register or sign in, and save shipping details on an unpaid order draft.

Payment completion and production deployment remain unfinished. Last verified: **2026-10-15**. See [RECOVERY_REVIEW.md](RECOVERY_REVIEW.md) for the interrupted-work review and recovery results.

## Current status

Implemented:

- Custom email-based accounts with live registration/sign-in forms and POST-only logout.
- Admin-managed departments, categories, subcategories, hero posters, products, and size-specific inventory.
- Department-aware catalog routes and keyword search across product names and descriptions.
- Catalog/search pagination with 12 products per page and stable ordering.
- Shared storefront layout, responsive homepage, category directory, product-detail gallery, account pages, and shipping pages.
- POST-only cart additions, quantity updates, increases, decreases, and removals with CSRF protection and session isolation.
- Separate cart rows for each product/size, stock validation, and a live navigation bag count.
- Guest cart and saved shipping-draft access preserved when sign-in rotates the session key.
- Shipping validation, pending order/item snapshots, and read-only order details in Django Admin.
- Development SQLite, static/media configuration, and console email backend.

The catalog and cart work but retain minimal markup; they still need integration with the shared visual layout.

Not implemented:

- Stripe Checkout creation, payment webhooks, confirmed order completion, and inventory deduction.
- Delivery serviceability checks, shipping rates, and taxes.
- Transactional order notifications.
- Fabric/material, occasion, and sale-price fields.
- Production settings, storage, and deployment.

## Stack and architecture

Python 3.12, Django 6.1, SQLite, Pillow, and the Stripe SDK are pinned in `requirements.txt`. Django views render Django templates and use the ORM for database access.

`ecommerce/templates/app.js` and the remaining standalone React/CDN templates are visual references with hardcoded data. Live account pages use Django forms; product detail uses the app-namespaced template at `store/templates/store/product_detail.html`.

## Repository structure

```text
Backend/
|-- accounts/                  Email-based accounts and forms
|-- carts/                     Cart models, forms, services, views, and counter
|-- category/                  Catalog hierarchy, hero posters, and navigation
|-- orders/                    Shipping forms, draft orders, snapshots, and admin
|-- store/                     Products, inventory, catalog/search/detail views
|-- ecommerce/
|   |-- static/shali/          Storefront, product/account, and checkout assets
|   `-- templates/            Shared layout, live pages, and old prototypes
|-- media/                     Local uploads; ignored by Git
|-- manage.py
|-- requirements.txt
|-- README.md
|-- HANDOFF.md
|-- RECOVERY_REVIEW.md
|-- CART_IMPLEMENTATION.md
|-- SHIPPING_IMPLEMENTATION.md
|-- HOMEPAGE.md
`-- PRODUCT.md
```

## Domain rules

`accounts.Account` is the configured user model. Registration stores a hashed password, normalizes email to lowercase, checks duplicate emails, and activates the account immediately.

`Department → Category → SubCategory` defines the catalog. Categories may remain unassigned in Admin, but public navigation, listings, and search exclude incomplete department paths. Products may belong to multiple subcategories only within their own category.

Products store a name, description, integer rupee price, color, up to three images, size type, and availability. `ProductInventory` tracks non-negative stock for clothing sizes `s`, `xl`, and `xxl`, saree `free_size`, or unsized `no_size`.

A `Cart` is identified by the browser session key. A database constraint prevents duplicate product/size rows in one cart. Adding the same size increases quantity; different sizes stay separate. Cart changes validate stock but do not reserve or deduct inventory. Navigation counts active units rather than distinct rows, and browsing does not create a cart/session just to calculate the count.

Saving shipping details creates or refreshes a pending `Order` and its `OrderItem` snapshots. Snapshots preserve names, sizes, quantities, and prices. Paid orders and drafts with payment references cannot be overwritten by the shipping form. Saving leaves the cart and inventory intact and does not place an order.

## Routes

| URL | Name | Purpose |
| --- | --- | --- |
| `/` | `home` | Homepage |
| `/admin/` | Django Admin | Content, accounts, and order drafts |
| `/accounts/register/` | `accounts:register` | Registration |
| `/accounts/login/` | `accounts:login` | Sign in; safe local return URLs supported |
| `/accounts/logout/` | `accounts:logout` | POST-only logout |
| `/categories/` | `categories` | Expandable catalog directory |
| `/store/` | `store:store` | Catalog |
| `/store/search/?keyword=silk` | `store:search` | Name/description search; blank keywords return no results |
| `/store/category/<department_slug>/` | `store:products_by_department` | Department catalog |
| `/store/category/<department_slug>/<category_slug>/` | `store:products_by_category` | Category catalog |
| `/store/category/<department_slug>/<category_slug>/<subcategory_slug>/` | `store:products_by_subcategory` | Subcategory catalog |
| `/store/product/<department_slug>/<category_slug>/<product_slug>/` | `store:product_detail` | Product gallery and stock-aware add-to-bag form |
| `/carts/` | `cart` | Cart |
| `/carts/add_cart/<product_id>` | `add_cart` | POST product, size, and optional quantity |
| `/carts/items/<item_id>/update/` | `update_cart` | POST replacement quantity |
| `/carts/items/<item_id>/increase/` | `increase_cart` | POST one-unit increase |
| `/carts/items/<item_id>/decrease/` | `decrease_cart` | POST one-unit decrease; remove last unit |
| `/carts/items/<item_id>/remove/` | `remove_cart` | POST removal |
| `/checkout/shipping/` | `orders:shipping_details` | Collect and save delivery details |
| `/checkout/shipping/review/` | `orders:shipping_review` | Review this session's saved draft |

## Local setup

```powershell
git clone https://github.com/Divo15/Shaali-E-commerce.git
cd Shaali-E-commerce
py -3.12 -m venv env
.\env\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

For the existing workspace, use `D:\Backend\env\Scripts\python.exe`. On macOS/Linux, create the environment with `python3 -m venv env` and activate it with `source env/bin/activate`.

Open `http://127.0.0.1:8000/` and `http://127.0.0.1:8000/admin/`. Add catalog records and upload images through Admin; no automatic catalog seed migration is provided.

## Media and migrations

`MEDIA_ROOT` is `BASE_DIR / 'media'`, served under `/media/` during development. Uploaded media, SQLite databases, virtual environments, and collected static files are ignored by Git.

During recovery, 28 files were copied from the old `store/media/` directory to `media/`, preserving the originals. All 24 database image references now resolve. Both media locations are ignored. Fresh environments need their own uploads or an explicit copy of existing media.

The existing migrations `carts.0002_cartitem_size` and `orders.0002_shipping_details` are applied in the local database. Run `migrate` in other environments. Legacy clothing cart rows have no recorded size and must be removed and re-added; free-size and unsized rows receive their known size.

## Validation

Verified on 2026-10-15:

```powershell
.\env\Scripts\python.exe manage.py check
.\env\Scripts\python.exe manage.py makemigrations --check --dry-run
.\env\Scripts\python.exe manage.py migrate --check
.\env\Scripts\python.exe manage.py test --verbosity 1
git diff --check
```

All **89 tests pass**, Django reports no system-check issues, and there is no migration drift or pending migration. Tests cover catalog/search/detail rendering, stock rules, cart mutations and isolation, bag counts, registration/login/logout, CSRF, safe redirects, shipping snapshots, and Admin access.

A browser check at 1440px and 390px verified product and account pages, add-to-bag, shipping save/review, registration, sign-in, and guest-cart preservation using a temporary database copy. No local asset failures, page script errors, or horizontal overflow occurred on the checked pages. Screenshots were visually inspected.

## Remaining work

1. Integrate the catalog and cart with the shared storefront layout.
2. Build payment completion around the existing draft-order models, rechecking price and stock before payment and fulfilment.
3. Calculate delivery charges/serviceability and send confirmed order notifications.
4. Add the deferred catalog fields and corresponding Admin/UI support.
5. Move secrets and environment-specific settings into environment variables and prepare production database/storage/deployment.

The current `SECRET_KEY`, `DEBUG`, and `ALLOWED_HOSTS` are development settings. The console email backend is configured, but order-email workflows are not implemented.

## Documentation

- [HANDOFF.md](HANDOFF.md): current development state and next tasks.
- [RECOVERY_REVIEW.md](RECOVERY_REVIEW.md): defects found, recovery actions, backup, and verification.
- [CART_IMPLEMENTATION.md](CART_IMPLEMENTATION.md): cart routes and migration behavior.
- [SHIPPING_IMPLEMENTATION.md](SHIPPING_IMPLEMENTATION.md): shipping validation and draft-order behavior.
- [HOMEPAGE.md](HOMEPAGE.md): storefront assets and homepage behavior.
- [PRODUCT.md](PRODUCT.md) and [detailed product requirements](ecommerce/templates/PRODUCT.md): brand direction and catalog requirements.

Keep migrations with model changes, test backend behavior, preserve the custom user model, and keep local data and secrets out of Git.
