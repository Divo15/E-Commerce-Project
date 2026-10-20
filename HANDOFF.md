# Project Handoff

Last verified: **2026-10-15**. The interrupted-work review is complete; see [RECOVERY_REVIEW.md](RECOVERY_REVIEW.md).

## Environment

- Repository: `https://github.com/Divo15/E-Commerce-Project.git`
- Branch: `testing`
- Workspace: `D:\Backend`
- Python: 3.12.13 in `env`
- Framework: Django 6.1
- Database: SQLite, `db.sqlite3`
- Upload root: `media/`

## Verified state

All 90 tests pass. Django system checks, migration drift checks, pending-migration checks, and `git diff --check` pass.

Local migrations include `store.0008_alter_product_size_type`, `category.0009_heroposter`, `carts.0002_cartitem_size`, and `orders.0002_shipping_details`. The shipping migration was applied during recovery after backing up SQLite.

The current local catalog contains eight products. All 24 database image references resolve after restoring 28 files from `store/media/` to the configured `media/` root. Originals remain in place. Both upload locations are ignored by Git.

## Working flows

- Admin-managed department/category/subcategory navigation, category imagery, and hero posters.
- Responsive homepage and category directory with desktop menus and mobile bottom navigation.
- Department-aware catalog/search with 12-product pagination, live image cards, stocked size choices, and a two-column phone grid.
- Product detail with up to three images, price, description, stock-aware size choices, and add-to-bag.
- Shared-layout session cart with item images, POST-only quantity/removal controls, a responsive summary, stock warnings, and CSRF protection.
- Shipping navigation is disabled until unavailable, invalid-size, or over-stock rows are corrected or removed; server-side shipping checks remain authoritative.
- Live bag count; sign-in preserves the guest cart and access to its saved shipping draft.
- Registration, email sign-in, safe local return URLs, and POST-only logout.
- Shipping-address form, current-session review, pending order/item snapshots, and read-only Admin details.

Shipping saves do not place orders, take payment, clear the cart, deduct stock, or send notifications.

## Code and templates

- `ecommerce/templates/base.html` and `includes/`: shared layout.
- `home.html`, `categories.html`, `signin.html`, and `register.html`: live Django pages.
- `store/templates/store/product_detail.html`: live product detail.
- `ecommerce/templates/store/store.html` and `carts/templates/carts/cart.html`: responsive catalog/search and bag pages using the shared storefront layout.
- `orders/templates/orders/`: shipping and review.
- `ecommerce/static/shali/`: storefront CSS/JS, product/account CSS, checkout CSS, brand and hero assets.
- `carts/context_processors.py`: session-scoped active-unit counter, registered in settings.
- Remaining root React/CDN templates and `app.js`: old visual references.

Public navigation and listings omit categories/products without a department path. Data remains manageable through Admin; no seed migration was added.

## Commands

```powershell
cd D:\Backend
.\env\Scripts\python.exe manage.py check
.\env\Scripts\python.exe manage.py makemigrations --check --dry-run
.\env\Scripts\python.exe manage.py migrate --check
.\env\Scripts\python.exe manage.py test --verbosity 1
.\env\Scripts\python.exe manage.py runserver
```

The browser check used a separate temporary SQLite copy. Test accounts and draft orders were not added to the project database.

## Git and remaining work

Existing work was preserved. The cart/shipping implementation and recovery fixes are tracked together on the `testing` branch. Keep databases, media uploads, environments, and secrets out of Git.

Next tasks:

1. Implement Stripe Checkout, webhooks, confirmed-order completion, and inventory deduction.
2. Add delivery serviceability, rates, and confirmed order notifications.
3. Add fabric/material, occasion, and sale-price fields.
4. Prepare environment-based production settings, database, and storage.

See `CATALOG_IMPLEMENTATION.md`, `CART_IMPLEMENTATION.md`, `SHIPPING_IMPLEMENTATION.md`, `HOMEPAGE.md`, and the product briefs for detailed behavior and scope.
