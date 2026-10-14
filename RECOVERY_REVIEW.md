# Recovery review — 2026-10-15

The project was reviewed after an interrupted work session. Existing uncommitted
cart/shipping changes were preserved. No truncated Python files or merge-conflict
markers were found. Empty package initialization files and unused generated app
stubs are normal Django scaffolding.

## Findings and completed fixes

| Finding | Result |
| --- | --- |
| Unfinished cart counter: broken import, query typo, uninitialized count, missing registration | Replaced with a session-scoped active-unit aggregate, registered in settings, and displayed in shared navigation without creating sessions during browsing. |
| Account URL configuration included twice | Removed the duplicate; Django URL checks now pass. |
| Shipping migration existed but was not applied locally | Backed up SQLite and applied `orders.0002_shipping_details`. |
| All 24 database image references were missing from the configured media root | Copied all 28 existing media files to `media/`, retained originals, and verified identical hashes. Both upload locations are ignored by Git. |
| Product-detail route referenced a missing template | Added the shared-layout gallery, product information, stocked size choices, add-to-bag, and empty/out-of-stock states; homepage cards now link to it. |
| Sign-in served an unconnected React prototype | Replaced it with a CSRF-protected Django form, retained email/return URL on errors, and preserved the guest cart during session rotation. |
| Registration used old branding/layout and did not bind an empty POST | Connected it to the shared layout and field errors; empty submissions now show required errors. |
| Unassigned categories/products could crash catalog URL rendering | Excluded incomplete department paths from public navigation, catalog, and search. |
| Console email configuration used the unsupported `MAILERS` key | Configured Django's `EMAIL_BACKEND`; order-email workflows remain unfinished. |
| Markdown described completed functionality as missing and omitted recovery details | Updated README, handoff, cart/shipping notes, homepage notes, and both product briefs. |

## Data preservation

Before migration, a SQLite backup was created at:

```text
D:\CodexData\Temp\shaali-recovery\db-before-recovery-20261015-001145.sqlite3
```

The source database and existing catalog remain in place. Original uploads are
retained under `store/media/`; restored copies live under the configured `media/`
root. No files were deleted. The cart/shipping implementation and recovery fixes
are included together on the `testing` branch.

Browser verification used a separate SQLite copy at
`D:\CodexData\Temp\shaali-recovery\browser-check.sqlite3`.
Its test account/order did not enter the project database.

## Verification

- Parsed all 74 project Python files successfully during the initial audit.
- Initial suite: 71 tests passed, with a duplicate URL-namespace warning.
- Final suite: **89 tests passed**; 18 regression tests added for the repaired behavior.
- `manage.py check`: no issues.
- `manage.py makemigrations --check --dry-run`: no changes detected.
- `manage.py migrate --check`: no unapplied migrations.
- `git diff --check`: passed.
- Media: 24 references, zero missing files, zero copy hash mismatches.
- Desktop (1440px) and mobile (390px) browser checks: product/account rendering,
  add-to-bag, shipping save/review, registration, login, and guest-cart retention.
- Checked pages had no horizontal overflow, failed local asset requests, or page
  script errors. Product/account screenshots were visually inspected.

Screenshots are stored under `D:\CodexData\Temp\shaali-recovery\`.
The temporary test server is stopped after verification.

## Remaining planned work

Catalog/cart styling, Stripe payment completion and webhooks, confirmed inventory
deduction, delivery rates/serviceability, order notifications, deferred catalog
fields, and production deployment remain unfinished. They are documented in
[HANDOFF.md](HANDOFF.md) and [README.md](README.md).

Saving shipping details creates an unpaid draft; it does not confirm an order or
take payment.
