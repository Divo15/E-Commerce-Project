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
| `cart_items` | Active `CartItem` records for the current browser session. |
| `quantity` | Sum of the quantities of all active cart items. |
| `total` | Sum of all cart-item subtotals. |

Each `cart_item` exposes `product`, `quantity`, and the calculated `subtotal` property.

## Current behaviour

- A cart is identified by the Django session key.
- Adding the same product increments its existing cart-item quantity.
- An empty cart renders an empty-state message and a link back to the catalog.
- The cart has a smoke test covering its empty state, totals, quantity, and template selection.
- The current cart markup is intentionally minimal and does not yet inherit the shared Shali storefront layout.

## Next improvements

1. Add POST-only endpoints to increase, decrease, and remove cart items.
2. Add cart tests for an empty cart, totals, and quantities.
3. Require a selected product size before adding inventory-managed products.
4. Move the cart to the shared storefront layout and style it consistently with the homepage.
