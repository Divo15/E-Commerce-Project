# Product

## Register

brand

## Users
Premium ethnic fashion customers shopping for sarees, salwar suits, lehengas, and celebratory desi wear. They are often browsing for weddings, festive occasions, gifting, and statement wardrobe pieces, and they want confidence in quality, styling, and cultural richness before purchasing.

## Product Purpose
This storefront showcases premium desi fashion with an elegant, image-led experience that turns discovery into desire. It should help shoppers quickly explore categories, occasions, featured collections, and product details while making the brand feel trustworthy, celebratory, and high value.

## Brand Personality
Elegant, celebratory, premium. The voice should feel polished and culturally rooted, with a sense of occasion, craft, and modern luxury rather than minimal tech retail.

## Anti-references
This should not look like a generic electronics marketplace, a dark streetwear storefront, or a stripped-down SaaS landing page. Avoid cold utility styling, harsh neon accents, and overly minimalist layouts that erase the richness of desi fashion.

## Design Principles
1. Lead with occasion and emotion, not just transactions.
2. Let imagery, typography, and color express cultural richness without becoming cluttered.
3. Make premium quality feel immediate through spacing, hierarchy, and polished product framing.
4. Keep browsing effortless across categories, collections, and purchase steps.
5. Balance celebration with trust so the experience feels beautiful and dependable.

## Accessibility & Inclusion
Target WCAG AA contrast and clear keyboard-friendly navigation. Support reduced motion preferences, keep forms readable and straightforward, and use descriptive labels and alt text so shoppers of different comfort levels and abilities can browse and purchase confidently.

## Catalog and Product Requirements

### Catalog hierarchy

Use a three-level catalog hierarchy:

```text
Department → Category → Subcategory
```

Use a separate `Department` model for the top-level navigation groups:

```text
Women
├── Sarees
│   ├── Banarasi Sarees
│   ├── Kanjivaram / Kanchipuram Sarees
│   ├── Organza Sarees
│   ├── Maheshwari Sarees
│   ├── Georgette Sarees
│   ├── Modal Sarees
│   ├── Cotton Sarees
│   └── Kota Doria Sarees
├── Ethnic Wear
│   ├── Churidar
│   ├── 3-Piece Sets
│   └── 2-Piece Sets
└── Dresses & Tops
    ├── Gowns
    └── Tops

Kids
└── Kids Wear

Men
├── Dhoti
├── Pajama
└── Shirts

Jewellery
├── Necklaces
├── Bangles
└── Earrings
```

Keep the existing category and subcategory records. Existing saree data should be placed under `Women` and `Sarees`. New records will be added manually through Django Admin; do not create an automatic seed-data migration.

Categories must remain dynamic and manageable through Django Admin. Administrators should be able to add, edit, remove, and reorder departments, categories, and subcategories without changing application code.

### URLs and navigation

Use nested URLs with the `category` prefix:

```text
/store/
/store/category/women/
/store/category/women/sarees/
/store/category/women/sarees/banarasi-sarees/
/store/category/men/shirts/
/store/category/jewellery/earrings/
```

The desktop navigation should use dropdown menus for the complete hierarchy. The mobile experience has priority and should use a bottom navigation bar:

```text
Home | Categories | Search | Cart | Account
```

The mobile `Categories` item should open a dedicated categories page with expandable departments, categories, and subcategories. Use touch-friendly controls. Search should be visible in the navigation but its functionality can be implemented later.

### Product assignment

Every product must belong to a complete catalog path:

```text
Department → Category → Subcategory
```

A product may belong to multiple subcategories, but all selected subcategories must belong to the same category. A product must not be assigned across unrelated categories such as both sarees and necklaces.

### Product listing

Category pages should show products directly rather than showing a separate subcategory landing page first. Product cards should initially display:

- Main product image
- Product name
- Regular or sale price
- Availability
- Add-to-cart action

Use a two-column product grid on mobile. Users should be able to add products to the cart directly from product cards.

### Clothing sizes and inventory

Only clothing products support sizes. The available clothing sizes are:

```text
S, XL, XXL
```

Sarees may use `Free Size` where appropriate. Jewellery does not have size selection and uses quantity only.

Stock must be tracked separately for each clothing size, for example:

```text
S: 5
XL: 8
XXL: 3
```

Customers must select a clothing size before adding the item to the cart. Different sizes of the same product must be stored as separate cart items. Jewellery uses a simple product quantity without size selection.

### Product information

Products should support:

- Multiple images, including one main image and additional gallery images
- One color per product
- Fabric or material information, such as silk, cotton, georgette, or organza
- Occasion information, such as wedding, festival, party, casual, or office
- Regular price and sale price
- Quantity-based inventory

Do not add a brand field at this stage.

## Confirmed Decisions

These decisions were made during project planning and should be treated as the current product requirements:

- Use a separate `Department` model above `Category` and `SubCategory`.
- Use `Women`, `Men`, `Kids`, and `Jewellery` as departments.
- Preserve existing category data and allow new records to be added manually through Django Admin.
- Use department-prefixed catalog URLs such as `/store/category/women/sarees/`.
- Use desktop dropdown navigation and mobile-first navigation.
- Use mobile bottom navigation with `Home`, `Categories`, `Search`, `Cart`, and `Account`.
- Open `Categories` as a dedicated page with expandable departments, categories, and subcategories.
- Keep Search visible but defer search functionality.
- Show products directly on category pages rather than requiring a separate subcategory landing page first.
- Use a two-column mobile product grid.
- Allow adding products to the cart directly from product cards.
- Allow a product to belong to multiple subcategories, but only within the same category.
- Clothing products use sizes `S`, `XL`, and `XXL`.
- Sarees may use `Free Size`.
- Jewellery has no size selection.
- Clothing stock is tracked separately for each size.
- Different sizes of one product are separate cart items.
- Jewellery uses product quantity only.
- Products use one color.
- Products support regular and sale prices.
- Products should eventually support a main image and additional gallery images.
- Products should include fabric/material and occasion information.
- Do not add a brand field.

## Current Implementation Status

Implemented:

- `Department` model with unique name and slug.
- Optional department relationship on `Category`.
- Department, category, and subcategory Admin registration and category filtering in Admin.
- Department-aware catalog route structure.
- Category descriptions remain available.
- Subcategory descriptions remain available.
- Department descriptions are intentionally not used.
- Existing product image field, category image field, and session cart remain available.
- Product many-to-many subcategory assignments with same-category validation.

Deferred:

- Manual creation of departments and assignment of existing categories in Admin.
- Department/category/subcategory image fields beyond the existing category image field.
- Size and size-specific inventory models.
- Multiple product image gallery.
- Fabric, occasion, sale-price, and quantity-inventory fields.
- Mobile bottom-navigation UI and product-card UI integration.
