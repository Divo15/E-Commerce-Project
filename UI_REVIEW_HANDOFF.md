# Shali Collections UI Review Handoff

Last verified: **2026-10-20**

## Purpose

This file is the working handoff for reviewing and refining the storefront UI in another ChatGPT/Codex session. It focuses on the live Django interface, especially the homepage and mobile experience.

The current UI is functional and tested. Future work should be iterative: preserve the existing content and behavior, then improve the presentation. Do not replace or remove whole sections unless the user explicitly asks for that.

## Project Location

- Repository: `D:\Backend`
- Git branch: `testing`
- Framework: Django 6.1
- Python environment: `D:\Backend\env`
- Database: `D:\Backend\db.sqlite3`
- Local media: `D:\Backend\media`
- Homepage: `http://127.0.0.1:8000/`
- Admin: `http://127.0.0.1:8000/admin/`

The Git working tree already contains substantial uncommitted work across the backend, templates, CSS, JavaScript, tests, and documentation. **Do not reset, clean, checkout, or overwrite unrelated changes.**

## Start the Application

Run these commands in PowerShell:

```powershell
cd D:\Backend
.\env\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

If port `8000` is already occupied by an older project process, use another port:

```powershell
.\env\Scripts\python.exe manage.py runserver 127.0.0.1:8001
```

Always confirm that the browser is showing this repository's current homepage. The current HTML loads:

```text
/static/shali/landing.css?v=nuwaara-mobile-footer-v2-20261020
```

If a different stylesheet query appears, an older Django process or cached page is being viewed.

## Optional ngrok Preview

For visual review from another app or device:

```powershell
cd D:\Backend
$env:DJANGO_ALLOWED_HOSTS = "127.0.0.1,localhost,.ngrok-free.app"
.\env\Scripts\python.exe manage.py runserver 0.0.0.0:8000
```

In a second PowerShell window:

```powershell
ngrok http 8000
```

Use the generated HTTPS forwarding URL. Do not place the ngrok authentication token in source files, documentation, screenshots, or Git. The tunnel should be treated as temporary and stopped after review.

The ngrok preview is primarily for visual inspection. Re-test authenticated forms, cart mutations, and checkout locally if proxy/CSRF configuration has not been explicitly prepared for public tunnel use.

## Required Design Reference

Use the project's requested design skill before making public-facing UI changes:

```text
C:\Users\HELLO!\Documents\ChatGPT\Ranking DashBoard\nuwaara-burgundy-storefront\SKILL.md
```

Also follow the skill's referenced inspection notes and visual references. The intended direction is a refined burgundy fashion storefront—not a generic SaaS template or an overdecorated luxury mockup.

## User Expectations

- Improve existing sections rather than removing or replacing them.
- Keep all real navigation and Django-driven content intact.
- Make mobile layouts intentional, polished, and easy to scan.
- Avoid helper patch files or PowerShell scripts for code changes.
- Edit the real project files directly.
- Do not modify Markdown files unless documentation is explicitly requested.
- Show and explain the exact files changed after each UI pass.
- Verify the result in a real browser at mobile and desktop widths.
- Preserve backend behavior, template URLs, form actions, CSRF protection, and dynamic loops.

## Current Visual Direction

The active homepage uses:

- Burgundy, warm off-white, and restrained neutral tones.
- Editorial serif display typography with a clean sans-serif body face.
- Large campaign photography and generous whitespace on desktop.
- A compact, commerce-first presentation on mobile.
- Minimal motion with reduced-motion support.
- Clear underlined text links instead of excessive filled buttons.
- Real catalog photography and data from Django models.

Avoid:

- Glassmorphism, neon gradients, excessive shadows, floating cards, or generic AI-style bento layouts.
- Decorative elements that do not support browsing or shopping.
- Invented features, links, products, testimonials, shipping promises, or payment badges.
- Hiding useful content simply to make a mobile page shorter.
- Replacing existing functional navigation with static mockup content.

## Homepage Anatomy

The live homepage template is `ecommerce/templates/home.html`.

1. **Announcement bar**
   - Shows the Shali brand and Singapore/India presence.
   - Defined through the `announcement` template block.

2. **Shared header**
   - Desktop navigation, search, account, and bag actions.
   - Mobile menu button opens a real dialog drawer.
   - Template: `ecommerce/templates/includes/header.html`.

3. **Hero**
   - Uses the latest admin-managed `HeroPoster` when available.
   - Falls back to `ecommerce/static/shali/hero-campaign.webp`.
   - Mobile is intentionally a full-width square campaign image with a real CTA overlay.

4. **Collections**
   - Desktop uses a category index and preview image treatment.
   - Mobile uses a two-column image grid selected from up to four suitable categories.
   - All links are generated from actual category records.

5. **New arrivals**
   - Displays up to four currently available products with complete catalog paths.
   - Mobile uses a horizontal swipe rail with approximately two cards visible and a partial next-card cue.

6. **Campaign edits/story area**
   - Desktop has editorial copy and selected collection imagery.
   - Mobile uses stacked square campaign panels.

7. **Footer**
   - The original footer content remains present on every breakpoint.
   - Includes the “Make it yours” introduction, collection links, account links, large Shali wordmark, copyright, and back-to-top link.
   - On mobile it is restyled into a compact two-column link layout; it is not replaced by accordions or removed.

## Current Mobile Footer Contract

The mobile footer was the latest corrected area. Preserve these requirements:

- Keep the complete footer content visible.
- Keep the introductory copy and “Explore collections” link.
- Show Collections and Your Shali as two balanced columns.
- Keep tap targets comfortably sized.
- Keep the Shali wordmark, but scale and space it for a phone screen.
- Keep copyright and Back to top in the final row.
- Maintain strong light-on-burgundy contrast.
- Do not reintroduce the removed alternate `.landing-footer-mobile` implementation.

Current mobile footer styling starts around `ecommerce/static/shali/landing.css:219`.

## Responsive Contract

Primary breakpoints in `ecommerce/static/shali/landing.css`:

- Above `1100px`: full editorial desktop composition.
- `901px–1100px`: tightened desktop/tablet spacing.
- `601px–900px`: tablet navigation and reduced layout dimensions.
- `600px` and below: purpose-built mobile homepage.

Review at minimum:

- `320 × 720`
- `390 × 844`
- `768 × 1024`
- `1440 × 900`

At every size verify:

- `document.documentElement.scrollWidth === window.innerWidth`
- No clipped headings, buttons, prices, or navigation.
- Touch targets are at least approximately 44px where practical.
- Sticky header does not cover anchor destinations.
- Product and category names can wrap without breaking layout.
- Footer content remains readable and complete.

## UI File Ownership

### Shared storefront

- `ecommerce/templates/base.html`
  - Page shell, blocks, shared assets, skip link, header, and default footer.
- `ecommerce/templates/includes/header.html`
  - Desktop header and mobile drawer markup.
- `ecommerce/templates/includes/icons.html`
  - Shared SVG symbol definitions.
- `ecommerce/templates/includes/search_form.html`
  - Search dialog/form markup.
- `ecommerce/static/shali/storefront.css`
  - Global tokens, shared header, drawer, navigation, dialogs, and common storefront rules.
- `ecommerce/static/shali/storefront.js`
  - Shared search and mobile-menu interactions.

### Homepage only

- `ecommerce/templates/home.html`
  - Homepage structure and its custom footer override.
- `ecommerce/static/shali/landing.css`
  - Homepage desktop/mobile design and footer styling.
- `ecommerce/static/shali/landing.js`
  - Category previews, arrival effects, and homepage interactions.
- `ecommerce/views.py`
  - Homepage data selection and context.

### Catalog and cart

- `ecommerce/templates/store/store.html`
- `ecommerce/templates/store/includes/`
- `carts/templates/carts/cart.html`
- `ecommerce/static/shali/catalog-cart.css`

### Other customer flows

- `store/templates/store/product_detail.html`
- `orders/templates/orders/shipping_details.html`
- `orders/templates/orders/shipping_review.html`
- Account templates under `ecommerce/templates/`
- Supporting styles under `ecommerce/static/shali/`

Do not edit standalone React/CDN prototype templates or `ecommerce/templates/app.js` when changing the live Django storefront.

## Dynamic Homepage Data

The homepage view is `home()` in `ecommerce/views.py`.

- `hero_poster`: newest usable admin-managed poster.
- `home_categories`: all categories with a valid department.
- `hero_category`: prefers the category with slug `sarees`, otherwise the first illustrated category.
- `mobile_categories`: up to four illustrated categories, prioritizing department variety.
- `featured_categories`: up to three illustrated categories from distinct departments where possible.
- `products`: four latest available products with valid department paths.
- `departments`: provided globally for navigation/footer rendering.

Do not hardcode catalog names or image paths to imitate the current local database. Empty and partial catalog states are tested and must continue rendering safely.

## Existing Interactions

- Mobile menu uses a native `<dialog>` and returns focus to its trigger when closed.
- Escape closes the mobile menu.
- Search is a shared overlay/dialog interaction.
- Category preview controls update the desktop preview without breaking direct links.
- Mobile product listings scroll horizontally with snap behavior.
- Motion is disabled when `prefers-reduced-motion: reduce` is active.

When changing UI, preserve keyboard access, visible focus, meaningful labels, and native semantics.

## Change Workflow

For each requested visual change:

1. Confirm the exact page and breakpoint affected.
2. Inspect the current rendered page before editing.
3. Read the relevant template, page stylesheet, and shared stylesheet.
4. Preserve all existing content and behavior unless removal is explicitly requested.
5. Make the smallest direct change in the owning files.
6. Bump the relevant static asset query string after CSS or JavaScript changes so phones do not keep stale assets.
7. Render the actual page in Chrome at the required breakpoints.
8. Check closed/open/hover/focus states where applicable.
9. Run focused tests, then broader tests when the work is complete.
10. Report the exact files and behavior changed.

Do not create temporary `.patch` or `apply-backend.ps1` helper files. Browser screenshots may be saved to a temporary directory for inspection, but they should not be added to the repository.

## Validation Commands

Focused homepage tests:

```powershell
cd D:\Backend
.\env\Scripts\python.exe manage.py test ecommerce.tests.HomepageTests
```

Full validation:

```powershell
.\env\Scripts\python.exe manage.py check
.\env\Scripts\python.exe manage.py makemigrations --check --dry-run
.\env\Scripts\python.exe manage.py migrate --check
.\env\Scripts\python.exe manage.py test --verbosity 1
git diff --check
```

Current verified result: **94 tests pass**.

The LF/CRLF messages from `git diff --check` are line-ending warnings, not whitespace errors. Do not mass-normalize line endings as part of a UI task.

## Browser QA Checklist

- Confirm the correct Django process and stylesheet version.
- Hard-refresh after any asset query-string change.
- Check browser console for JavaScript errors.
- Check Network for missing local images, CSS, or JavaScript.
- Inspect mobile menu open, close button, backdrop, Escape behavior, and focus return.
- Inspect hero cropping at 320px and 390px.
- Confirm mobile category tiles remain two columns.
- Confirm the product rail scrolls and exposes the next-card cue.
- Confirm campaign text remains readable over every current image.
- Confirm all footer content is present at phone widths.
- Confirm there is no horizontal page overflow.
- Recheck desktop after every mobile CSS change.

## Known Product/Deployment Boundaries

The following are not finished and should not be represented as complete in the UI:

- Live payment completion and Stripe webhook processing.
- Final inventory deduction after payment.
- Singapore/India delivery serviceability and rate calculation.
- Taxes and confirmed shipping prices.
- Transactional order confirmation messages.
- Production database, storage, HTTPS, and deployment configuration.

Shipping currently saves an unpaid draft. It does not place a paid order, clear the bag, or deduct stock.

## Suggested Prompt for the Next ChatGPT Session

```text
Work in D:\Backend. Read UI_REVIEW_HANDOFF.md first, then read
C:\Users\HELLO!\Documents\ChatGPT\Ranking DashBoard\nuwaara-burgundy-storefront\SKILL.md.

Review the live Django homepage in a real browser at 390x844 and 1440x900.
I will point out UI changes one by one. Preserve all existing content and backend
behavior unless I explicitly ask for removal. Edit the real files directly; do not
create helper patch or PowerShell files. After each change, show the files changed,
verify mobile and desktop, and run the focused homepage tests.
```

## Final Cautions

- Never expose credentials, ngrok tokens, Django secrets, Stripe secrets, session cookies, or database contents.
- Do not commit or create branches unless explicitly requested.
- Do not delete existing documentation or unrelated working-tree changes.
- Do not claim a visual issue is fixed without inspecting the rendered page.
- Ask before changing product behavior, checkout behavior, or information architecture; ordinary styling changes can be implemented directly.
