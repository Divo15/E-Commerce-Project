# Shaali E-commerce

Shaali E-commerce is an in-progress Django storefront for premium Indian ethnic fashion. The project currently provides the backend foundation for accounts, categories, subcategories, products, and a session-based shopping cart. The customer-facing frontend, checkout flow, and production configuration are still under development.

## Project Status

This repository is an early-stage application, not a production-ready store.

Implemented:

- Django project and application structure
- Custom email-based user model
- Registration, login, and POST-only logout views
- Category and subcategory models and Django Admin configuration
- Product model and Django Admin configuration
- Session-based cart and cart-item models
- Add-to-cart and cart-total calculation logic
- SQLite development database configuration
- Static and media file configuration
- Department-aware catalog routes and filtering
- Shared Django storefront layout with responsive homepage and category directory
- Desktop department menus and mobile bottom navigation
- Initial order and order-item models, including Stripe reference fields
- Homepage, catalog, inventory, and cart smoke tests

Partially implemented:

- Product-detail view
- Cart display and add-to-cart flow
- Product listing template integration

Not implemented:

- Cart quantity update and item removal
- Search and pagination
- Checkout routes and order creation flow
- Payment processing and Stripe webhooks
- Transactional email
- Production deployment configuration

## Technology Stack

- Python 3.12
- Django 6.1
- SQLite for local development
- Pillow for image fields
- Django templates, CSS, and JavaScript for the current integrated-frontend direction

Dependencies are pinned in `requirements.txt`.

## Architecture

The current application is a Django monolith:

```text
Browser request
    -> Django URL resolver
    -> Django view
    -> Django ORM
    -> SQLite
    -> Django template
    -> HTML response
```

Django ORM queries are used throughout the project. No handwritten SQL is currently required.

The repository also contains React-style static design prototypes in `ecommerce/templates/app.js`. They use React from a CDN and hardcoded data, and they are not connected to the Django models, authentication, cart, or URL routing. Treat them as visual references until a final frontend architecture is selected.

## Repository Structure

```text
Backend/
|-- accounts/                 Custom user model and authentication
|-- carts/                    Session cart models and views
|-- category/                 Category and subcategory domain
|-- ecommerce/                Project settings, root URLs, and shared assets
|   |-- static/               Project CSS
|   `-- templates/            Current templates and design prototypes
|-- store/                    Product model, catalog views, and store URLs
|-- manage.py
|-- requirements.txt
|-- HANDOFF.md                Earlier development handoff notes
`-- README.md
```

## Domain Model

### Account

`accounts.Account` is the configured `AUTH_USER_MODEL`.

Important characteristics:

- Email is the login identifier.
- Username and email are unique.
- New users are created through `RegistrationForm`.
- Registered users are currently activated immediately.

### Category and SubCategory

`category.Category` contains the category name, slug, description, and optional image.

`category.SubCategory` belongs to a category through `category`. Subcategory slugs are unique within each category, enforced by a database constraint.

The intended initial hierarchy is:

```text
Sarees
|-- Banarasi
|-- Kanjipuram
|-- Organza
|-- Maheshwari
|-- Georgette
|-- Modal
|-- Cotton
`-- Kota Doria
```

### Product

`store.Product` currently belongs directly to a category and contains:

- Product name and slug
- Description and color
- Integer price
- Product image
- Size behavior (`Clothing sizes`, `Free size`, or `No size`)
- Availability flag
- Created and modified timestamps

Products can be assigned to multiple subcategories. Assignments are validated so
that every selected subcategory belongs to the product's category.

`ProductInventory` tracks a separate non-negative quantity for each sellable size.
Clothing products support `S`, `XL`, and `XXL`; sarees can use `Free Size`;
unsized products such as jewellery use a single `No size` inventory row.

### Cart and CartItem

`carts.Cart` is identified by the Django session key. `carts.CartItem` joins a cart to a product and stores quantity and active state.

The database prevents duplicate product rows within the same cart. Adding an existing product increments its quantity. `CartItem.subtotal` calculates `product.price * quantity`.

The current cart view calculates the total value and total quantity, but its template path and template context integration are intentionally unfinished while the frontend direction is being decided.

## Current Routes

Routes currently connected by `ecommerce/urls.py`:

| URL | Name | Purpose |
| --- | --- | --- |
| `/` | `home` | Responsive Shali storefront homepage |
| `/admin/` | Django Admin | Content and account administration |
| `/accounts/register/` | `accounts:register` | Account registration |
| `/accounts/login/` | `accounts:login` | Account login |
| `/accounts/logout/` | `accounts:logout` | POST-only logout |
| `/categories/` | `categories` | Expandable department/category/subcategory directory |
| `/store/` | `store:store` | Catalog listing |
| `/store/category/<department_slug>/` | `store:products_by_department` | Department catalog listing |
| `/store/category/<department_slug>/<category_slug>/` | `store:products_by_category` | Category catalog listing |
| `/store/category/<department_slug>/<category_slug>/<subcategory_slug>/` | `store:products_by_subcategory` | Subcategory catalog listing |
| `/store/product/<department_slug>/<category_slug>/<product_slug>/` | `store:product_detail` | Product-detail route (template still pending) |
| `/carts/` | `cart` | Cart summary view |
| `/carts/add_cart/<product_id>` | `add_cart` | Add or increment a product |

The current catalog route design is:

```text
/store/
/store/category/<category_slug>/
/store/category/<category_slug>/<subcategory_slug>/
/store/product/<category_slug>/<product_slug>/
```

Explicit `category/` and `product/` prefixes prevent subcategory and product routes from competing for the same two-slug URL pattern.

## Local Setup

### 1. Clone the repository

```powershell
git clone https://github.com/Divo15/Shaali-E-commerce.git
cd Shaali-E-commerce
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
py -3.12 -m venv env
.\env\Scripts\Activate.ps1
```

macOS or Linux:

```bash
python3 -m venv env
source env/bin/activate
```

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Apply migrations

```powershell
python manage.py migrate
```

### 5. Create an administrator

```powershell
python manage.py createsuperuser
```

The custom user manager asks for first name, last name, email, username, and password.

### 6. Run the development server

```powershell
python manage.py runserver
```

Open `http://127.0.0.1:8000/` for the site and `http://127.0.0.1:8000/admin/` for Django Admin.

## Useful Development Commands

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py showmigrations
python manage.py test
python manage.py runserver
```

The committed SQLite database, uploaded media, collected static files, virtual environments, and environment files are excluded by `.gitignore`. Each developer must run migrations and create their own local data.

## Frontend State

The frontend is currently mixed while the customer-facing layout is being consolidated.

- `home.html`, `base.html`, the shared includes, and `categories.html` are live Django templates.
- The homepage reads the Department → Category → SubCategory hierarchy dynamically from Django Admin data.
- The homepage uses category imagery, a generated promotional hero image, keyboard-accessible department menus, and reduced-motion support.
- `register.html` uses a real Django form and static-file tag.
- Several root templates are static React CDN prototypes.
- Prototype navigation uses relative `.html` links instead of Django named URLs.
- Prototype product and cart data is hardcoded.
- Some Django views reference template paths that do not currently exist.

For an integrated Django frontend, the recommended structure is:

```text
ecommerce/templates/
|-- base.html
`-- includes/
    |-- header.html
    `-- footer.html

store/templates/store/
|-- product_list.html
`-- product_detail.html

accounts/templates/accounts/
|-- login.html
`-- register.html

carts/templates/carts/
`-- cart.html
```

Use Django template inheritance, `{% static %}`, `{% url %}`, and server-rendered context data. Small JavaScript components can be added for interactions without separating the frontend.

If the project later adopts Next.js or standalone React, keep Django as the backend and expose the existing domain through Django REST Framework. The models, migrations, admin configuration, and most business rules can remain; the Django page views and templates would be replaced or supplemented by API endpoints.

## Known Issues

These issues are present in the current code and should not surprise the next developer:

1. `store.views.product_detail()` has the correct slug lookup, but `store/product_detail.html` has not been created.
2. Homepage product cards link to their collection until the product-detail template is implemented.
3. `carts.views.add_cart()` raises a server error for an invalid product ID instead of returning 404.
4. Cart quantity updates, removals, and size-specific cart items are not implemented.
5. The login template is still a static React prototype and is not wired to the Django login form fields.
6. The configured email setting is named `MAILERS`; Django normally expects `EMAIL_BACKEND` or an appropriate installed-package configuration.
7. Orders have models and a migration, but there are no checkout views, payment calls, webhook handlers, or order tests.
8. `SECRET_KEY`, `DEBUG`, and `ALLOWED_HOSTS` are development values and are not production-safe.

## Recommended Next Steps

Complete work in this order to avoid building UI on unstable routes:

1. Build `store/product_detail.html` using the shared storefront layout.
2. Finish product cards and catalog pages with live images, prices, and add-to-cart actions.
3. Add cart quantity update, removal, and selected-size support.
4. Build the checkout, order creation, Stripe session, and webhook workflow around the existing order models.
5. Wire the account templates into the shared layout and Django forms.
6. Add tests for product detail, cart mutations, account flows, and orders.
7. Move secrets and environment-specific settings into environment variables.
8. Switch to PostgreSQL and production storage when preparing deployment.

## Validation

At the time of this README update, the following command passes:

```powershell
.\env\Scripts\python.exe manage.py check
```

The focused suite currently covers the homepage, department filtering, category/subcategory routing, product inventory, and an empty cart. Run the full suite before production changes.

## Product Direction

The design brief is stored in `ecommerce/templates/PRODUCT.md`. The storefront implementation notes are in `HOMEPAGE.md`. The intended experience is elegant, celebratory, premium, and culturally rooted, with accessible navigation and strong product imagery for sarees and other occasion wear.

Target WCAG AA contrast, keyboard-friendly navigation, descriptive image alternatives, readable forms, and reduced-motion support.

## Development Notes

- Keep changes focused and create migrations for every model change.
- Run `manage.py check` before committing.
- Add tests alongside new backend behavior.
- Do not commit the virtual environment, local database, uploaded media, collected static files, or secrets.
- Prefer Django ORM queries over raw SQL unless profiling demonstrates a specific need.
- Preserve the existing custom user model; changing `AUTH_USER_MODEL` after migrations is expensive.
- Explain architectural changes before implementing them when collaborating with the project owner.
