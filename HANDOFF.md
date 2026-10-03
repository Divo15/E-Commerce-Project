# Project Handoff

## Overview

- Repository: `https://github.com/Divo15/Shaali-E-commerce.git`
- Branch: `testing`
- Project path: `D:\Backend`
- Framework: Django 6.1
- Python: 3.12
- Virtual environment: `env`
- Database: SQLite (`db.sqlite3`)

## Current Validation

The following command currently passes:

```powershell
.\env\Scripts\python.exe manage.py check
```

Applied migrations include the latest `category`, `store`, and `orders.0001_initial` migrations.

## Completed Work

- Department-aware catalog URLs are connected from `ecommerce/urls.py`.
- Department, category, and subcategory menus are supplied by `category.context_processor.menu_links`.
- Department catalog pages filter products to the selected department.
- A reusable Django storefront layout, header, footer, home page, and categories directory are live.
- Desktop navigation exposes the full Department → Category → SubCategory hierarchy; mobile navigation links to `/categories/`.
- The homepage uses live category data and media, a branded hero image, empty states, and accessible reduced-motion behavior.
- The cart template and context are wired at `carts/templates/carts/cart.html`.
- `orders` is installed, migrated, and has initial `Order` and `OrderItem` models ready for checkout work.
- Focused homepage, catalog/inventory, and cart smoke tests exist.

## Current Catalog Models

`Department` contains a name and slug. `Category` belongs to an optional department and contains:

- `category_name`
- `slug`
- `description`
- `category_image`

`SubCategory` belongs to a category. `Product` belongs to a category, may belong to multiple subcategories in that category, and uses size-specific inventory.

- `category` foreign key
- `subcategory_name`
- `slug`
- `description`

The intended initial hierarchy is:

- Sarees
  - Banarasi
  - Kanjipuram
  - Organza
  - Maheshwari
  - Georgette
  - Modal
  - Cotton
  - Kota Doria

Records are managed through Django Admin. The local database currently includes Woman, Man, Kids, and Jewellery departments with category imagery; product records have not yet been added.

## Current Routes

- `/` renders the Shali homepage.
- `/categories/` renders the expandable catalog directory.
- `/store/` and `/store/category/<department>/<category>/<subcategory>/` serve the catalog hierarchy.
- `/carts/` renders the session cart.
- `/accounts/` serves registration, login, and POST-only logout routes.
- The product-detail route exists, but its template is still missing.

## Templates

- `ecommerce/templates/base.html` and `ecommerce/templates/includes/` hold the shared storefront chrome.
- `ecommerce/templates/home.html` and `ecommerce/templates/categories.html` are responsive, live Django templates.
- `ecommerce/static/shali/` holds the storefront CSS, browser interactions, logo, and hero image.
- `HOMEPAGE.md` explains asset provenance, dynamic content rules, and verification steps.
- `ecommerce/templates/store/store.html` remains a minimal catalog template.
- The larger static React-style templates are not connected to Django routes.
- Several static templates use relative `styles.css`, `app.js`, and `.html` links that will not resolve correctly through Django without static tags and named URLs.

## Git State

The repository has established commits and a remote `testing` branch. Do not stage the local virtual environment, SQLite database, media uploads, collected static files, or environment secrets; `.gitignore` excludes them.

## Useful Commands

```powershell
cd D:\Backend
.\env\Scripts\Activate.ps1
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py showmigrations
python manage.py runserver
python manage.py test ecommerce store carts
```

## Next Work

1. Create `store/templates/store/product_detail.html` and link homepage/catalog product cards to it.
2. Replace the minimal catalog and cart markup with the shared layout.
3. Implement cart mutations and required size selection.
4. Build checkout and Stripe integration on the new order models.
5. Add order, cart-mutation, product-detail, and authentication tests.
