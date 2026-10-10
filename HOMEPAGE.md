# Shali homepage

The homepage and `/categories/` use Django templates, with shared markup in
`ecommerce/templates/base.html` and `ecommerce/templates/includes/`.
Styles and small browser interactions live in `ecommerce/static/shali/`.
The supplied logo is stored unchanged as `shali/brand.jpg`.

## Visual direction

The reference video informed the image-led hero, circular category navigation,
collection panels, and new-arrivals section. The original composition uses the
logo's burgundy and warm gold, Prata display lettering and Manrope body text,
with restrained entrance/hover movement and reduced-motion support.
Web fonts load from Google Fonts with local serif/sans-serif fallbacks.

## Content

- Navigation reads Department → Category → SubCategory from Django Admin data.
- `/categories/` provides an expandable, mobile-friendly catalog directory.
- Homepage categories must have a department assigned. No catalog data is seeded.
- Upload a hero image and descriptive alt text in Django Admin under
  **Category > Hero posters**. The newest poster with an image is displayed;
  editing that record updates the current campaign. Wide images around 2:1 work
  best with the existing layout. Keep the left side clear for the headline.
- When no poster is uploaded, the hero uses
  `ecommerce/static/shali/hero-campaign.webp`, an original generated
  campaign photograph with a model on the right and headline overlaid on the left.
  Desktop navigation overlays the photograph; mobile keeps a solid readable header
  and places the copy over the lower portion of the photograph.
- Hero photography is promotional, not a specific product listing. Its CTA opens
  the live category directory. The saree category is still used to avoid repeating
  that category in the collection panels when other illustrated categories exist.
- Collection panels use the first illustrated non-hero category from each
  department, up to three. Catalog order follows record creation order.
- New arrivals display the four newest available products with complete
  department/category paths. An empty catalog shows an honest empty state.
- Upload category images through Django Admin. Existing media remain local;
  the repository ignores `media/`, so another environment needs its own uploads.
- Search is visibly marked as coming soon, with a working category-browsing link.

## Scope

This change styles the homepage and category directory. Existing store, product
detail, account, and cart pages retain their current implementation. In particular,
`store/product_detail.html` is still a follow-up task; homepage product cards link
to their category until that page is implemented. Cart size selection, checkout,
search, newsletter subscriptions, reviews, and shipping policies are not invented.

## Checks

Run `python manage.py check` and `python manage.py test ecommerce store carts`.
Review `/` and `/categories/` at desktop, tablet, and phone widths. Verify dropdown
keyboard access, Escape dismissal, the search notice, category expansion, image
fallbacks, and the mobile bottom navigation.

The department catalog view now filters products by the selected department;
the new navigation regression test covers isolation between departments.

## Hero asset provenance

Asset: `ecommerce/static/shali/hero-campaign.webp` (1774 × 887, about 156 KiB).
Created with the built-in image generation tool, then encoded as WebP for delivery.
The photograph illustrates the brand rather than advertising a specific inventory item.

Generation prompt:

> Use case: ads-marketing. Create one photorealistic website hero background image for Shali Collections, an Indian ethnic fashion boutique. Wide landscape 2:1 composition (prefer 2048x1024). A poised adult Indian woman in a rich burgundy-red silk saree with intricate golden zari borders, wearing understated gold traditional earrings, standing in a warm sandstone palace courtyard with ornate carved pillars and softly receding arches. Fashion campaign photography, authentic fabric detail, soft warm late afternoon light, natural realistic face and hands. Crucial layout: model placed around 74 percent of the image width, head visible in upper right third, framed from head to below the knees, her red drape fills right side. Entire LEFT HALF is quiet dark warm architectural negative space suitable for white website headline text, with visible but unobtrusive shadowed arches. Make scene continuous across full width, NOT a split panel, not a collage. Photographic tones warm brown, burgundy, antique gold. Premium calm mood. NO text, lettering, logos, watermarks, buttons, UI, typography, borders, or inset images. This is promotional campaign imagery, not a specific product listing. Do not use any existing logo image as the background.
