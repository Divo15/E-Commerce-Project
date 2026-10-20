# Catalog and cart storefront integration

Verified on **2026-10-15**. Catalog, search, and bag pages inherit the established
Shali layout, typography, burgundy/gold palette, navigation, and footer.

## Catalog

- Templates: `ecommerce/templates/store/store.html` and the reusable
  `store/includes/product_card.html` partial.
- Cards use real product images, names, integer rupee prices, availability,
  and POST add-to-bag forms.
- Clothing requires a stocked size. Free-size/unsized products omit size selection.
- Missing/zero/incompatible inventory shows an out-of-stock state with no add form.
- Images and names link to product detail. Missing images have an explicit fallback.
- Department/category/subcategory routes retain their existing filtering.
- Catalog/search preserve 12-product pagination and query parameters.
- Search in the page and the shared dialog use distinct input IDs.
- The grid has four desktop columns, three at intermediate widths, and two on phones.
  Collection links scroll horizontally on smaller screens.

`store.views._add_stock_context` prepares display stock from prefetched inventory
for paginated products and product detail. The existing cart services still enforce
all posted sizes and quantities on the server.

## Bag

- Template: `carts/templates/carts/cart.html`.
- Active items show image, name, selected size, unit price, subtotal, and stock state.
- Native POST forms support minus/plus, manual quantity updates, and row removal.
  Controls remain labeled for keyboard and assistive-technology use.
- Unavailable or unassigned products are displayed without a broken detail link.
- The summary shows the item subtotal and unconfirmed delivery charges.
- Any existing stock/size warning disables the shipping link until corrected or
  removed. Server-side shipping validation remains in place.
- Summary sits alongside items on desktop and below them on phones.
- Empty bags and validation messages use the shared layout.

## Assets and verification

Styles are in `ecommerce/static/shali/catalog-cart.css`, alongside the existing
`storefront.css` and `commerce.css`. Existing reduced-motion rules cover shared
transitions. No new JavaScript dependency or schema migration is required.

- All **90 tests pass**.
- Django system checks and migration drift checks pass.
- Browser widths: 1440, 1024, 768, 390, and 320px.
- Verified pagination, search dialog, category routes, stocked/unsized additions,
  unavailable-stock and missing-image states, quantity changes, removal, and
  shipping access after stock correction.
- No horizontal page overflow, duplicate IDs, failed local assets, or script errors
  occurred in the checked flows.
- Primary body text colors exceed 4.5:1 against the main background.
- Desktop and phone screenshots were visually inspected.

Preview data were created only in a temporary SQLite copy. Scripts, database,
and screenshots are under `D:\CodexData\Temp\shaali-catalog-cart\`.
The preview server is stopped after verification.

Payment processing, delivery calculation, and confirmed-order notifications remain
separate follow-up work; see [HANDOFF.md](HANDOFF.md).
