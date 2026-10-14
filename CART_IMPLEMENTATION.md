# Cart page implementation

The cart route is served by `carts.views.cart` at `/carts/`.

## Template location

The view renders `carts/cart.html`. Django finds it at:

```text
carts/templates/carts/cart.html
```

Using an app-namespaced template path avoids collisions with templates owned by other apps.

## Context provided to the template

| Variable | Meaning |
| --- | --- |
| `cart_items` | Active, size-specific `CartItem` records for the current browser session. |
| `quantity` | Sum of the quantities of all active cart items. |
| `total` | Sum of all cart-item subtotals. |

Each `cart_item` exposes `product`, `size`, `quantity`, and the calculated
`subtotal` property. The cart view also provides `available_quantity` and
`stock_message` for each row, so stock changes are visible to the shopper.

## Current behaviour

- A cart is identified by the Django session key. Sign-in carries the existing cart
  to Django's rotated session key, retaining its items and saved shipping draft.
- Clothing requires a posted `size` of `s`, `xl`, or `xxl` before adding.
- Free-size products automatically use `free_size`; jewellery uses `no_size`.
- Adding the same product and size increments its existing quantity. Different
  sizes of one product remain separate rows, enforced by a database constraint.
- Adding, updating, and increasing quantities validate product availability and
  the current inventory for the selected size. Missing or zero inventory cannot
  be added. Cart additions do not reserve or deduct stock; checkout must recheck it.
- Cart mutations accept POST only, use Django CSRF protection, and restrict item
  access to the current browser session. Invalid product/item IDs return 404.
- Quantity updates require positive integers. Decreasing a quantity of one
  removes the row; a separate removal action deletes the whole selected row.
- An empty cart renders an empty-state message and a link back to the catalog.
- Catalog and search results include add-to-cart forms and stocked clothing sizes.
- Product detail also provides stock-aware size selection and add-to-bag.
- `carts.context_processors.counter` supplies `cart_count` to the shared layout.
  It sums active units only for the current session, returns zero for an empty bag,
  and does not create a session/cart during browsing. Header and mobile navigation
  display the count; the desktop badge shows `99+` for larger quantities.
- The cart displays errors and POST forms for quantity changes and removal.
- Tests cover sizes, stock limits, totals, session isolation, CSRF, request methods,
  inactive items, legacy items, catalog forms, and the data migration.
- The current cart markup is intentionally minimal and does not yet inherit the shared Shali storefront layout.

## Mutation routes

| Route | Name | Posted fields |
| --- | --- | --- |
| `/carts/add_cart/<product_id>` | `add_cart` | `size` for clothing; optional `quantity` (defaults to 1) |
| `/carts/items/<item_id>/update/` | `update_cart` | `quantity` |
| `/carts/items/<item_id>/increase/` | `increase_cart` | None |
| `/carts/items/<item_id>/decrease/` | `decrease_cart` | None |
| `/carts/items/<item_id>/remove/` | `remove_cart` | None |

## Existing carts

Apply `carts.0002_cartitem_size` with `python manage.py migrate`. Existing free-size
and unsized rows receive their known size. Existing clothing rows keep their
quantities and an empty size because the original cart did not record a choice.
Those rows show a request to remove and re-add the product with a selected size.

## Validation

Run `python manage.py test carts` and `python manage.py makemigrations --check --dry-run`.
Verified on 2026-10-15 as part of the passing 89-test suite. Shipping-address
collection and draft review are implemented; see `SHIPPING_IMPLEMENTATION.md`.
Shared catalog/cart styling and payment completion remain follow-up work.
