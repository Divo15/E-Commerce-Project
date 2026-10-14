# Shipping details

Customers can open shipping details from their bag at `/checkout/shipping/`.
The form collects recipient name, email, phone, address, city, state/province,
PIN/postal code, country, and optional locality, landmark, and delivery instructions.

Required fields, email, phone, address lengths, and postal-code syntax are checked
on the server. Indian PIN codes must contain six digits and cannot start with zero.
International postal codes allow letters, numbers, spaces, and hyphens. This is
format validation; delivery serviceability and shipping rates are not calculated.

## Saving

- GET displays the form and does not create an order.
- POST validates the current session's active cart and rechecks size-specific stock.
- Valid details are saved on a pending `Order`, alongside snapshots of product
  names, sizes, quantities, and prices in `OrderItem`.
- Repeated saves update that session's pending draft and refresh its item snapshot.
- Orders that are paid or have payment references are never edited by this form.
- Saving does not clear the cart, deduct inventory, take payment, or send email.
- `/checkout/shipping/review/` displays only the current session's saved draft.
- Shipping and review responses disable browser caching.
- Sign-in preserves the guest cart through session-key rotation, so its saved
  draft remains accessible from the same browser.

The review page explicitly says the order has not been placed. Future payment
integration must revalidate cart prices and stock, calculate delivery charges,
confirm payment, and then send owner/customer notifications.

## Owner access

Orders are registered in Django Admin with shipping contact/address details,
payment status, and read-only item snapshots. Pending drafts are unpaid; the
owner should fulfil only orders whose payment is confirmed. Customers cannot
read another browser session's address by changing an order ID.

## Database and checks

The model changes are in `orders/models.py`; the existing migration is
`orders.0002_shipping_details`. Apply it with `python manage.py migrate` in a fresh
or older environment. It was applied to the local database during recovery on
2026-10-15 after creating a SQLite backup. Legacy records retain blank shipping fields.

Run `python manage.py test orders carts`, followed by the full suite.
On 2026-10-15, all 89 project tests passed and no migrations were pending.
A browser check on a temporary database copy verified address saving, draft review,
and continued draft access after registration/sign-in. No test order was created
in the project database. See `RECOVERY_REVIEW.md` for verification details.
