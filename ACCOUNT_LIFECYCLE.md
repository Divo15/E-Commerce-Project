# Account lifecycle

Google signup/sign-in is now the primary entry point. See
[GOOGLE_SIGNIN_SETUP.md](GOOGLE_SIGNIN_SETUP.md) for the owner's configuration
step, identity-linking rules, and customer onboarding. The email/password
lifecycle below remains available as an alternative; Google-only accounts do
not require store verification email or a store password.

Registration creates an inactive account awaiting email verification. The email
address is the customer's sign-in identifier; customers do not choose a username.
An internal unique username is generated automatically for database compatibility.
The email
link opens a confirmation screen; its CSRF-protected button activates the account.
Verification links expire in one hour and become invalid after activation,
password changes, or email changes. Existing active accounts remain usable.
Administratively disabled accounts cannot be reactivated using the resend flow.

The account icon and footer open `/accounts/`, which requires sign in and offers
contact-detail editing, password change and a POST-only sign-out button. Sign in accepts email without
case sensitivity and keeps the guest cart and shipping draft. Password change
keeps this device's session and cart; other sessions expire on their next request.
Password reset requires sign in again and invalidates existing sessions.

## Saved bags and shipping drafts

Each customer has one account-owned cart. It survives logout, cookie deletion,
session expiry, password recovery, and switching devices. Guests still have
browser-session bags. Signing in attaches a guest bag to the account or merges
it into the existing saved bag. Matching product/size quantities are added;
different sizes remain separate. Guest merging is consumed once. A quantity
above current stock stays visible with a warning and must be corrected before
shipping can be saved. A bag is not a stock reservation.

Shipping drafts follow the account/cart, not a browser-session pointer. The
latest unpaid draft without payment references is restored on another device.
Merging or editing the bag requires saving shipping details again before review.
Paid/payment-linked orders are never reused as drafts. Signing out exposes an
empty guest bag rather than the signed-out customer's items or address.

Legacy carts with a current authenticated session are adopted on first access
or logout. Previously abandoned anonymous carts cannot be assigned to a person
without proof of ownership; they remain guest carts. No catalog data is seeded.

Recovery requests have a generic response for unknown/inactive addresses.
Database-backed fixed-window limits cover registration, verification resends,
password recovery, and sign-in attempts. Limits use server-provided REMOTE_ADDR
and a hashed email identity; raw addresses are not stored in the limit table.
Through a local ngrok agent, all users can share the same IP budget. Production
deployments should configure trusted proxy client addresses and tune limits.

## Local email

In DEBUG mode, default email delivery writes messages to `.local/emails/`.
Open a saved message and follow its verification/reset link. This is a real
application flow with a local mail sink; messages are not delivered to inboxes.
The ignored `.local/secret_key` keeps local sessions/tokens valid across restarts.
Never serve `.local` through static files or upload it to Git.

## Inbox delivery

Set these environment variables before launching the app (the app does not
automatically source `.env` files):

```text
DJANGO_EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=<your provider's SMTP host>
EMAIL_PORT=587
EMAIL_HOST_USER=<SMTP user>
EMAIL_HOST_PASSWORD=<SMTP secret>
EMAIL_USE_TLS=true
EMAIL_USE_SSL=false
DEFAULT_FROM_EMAIL=Shali Collections <verified-sender@your-domain>
ACCOUNT_PUBLIC_ORIGIN=https://your-store-domain
```

For a production HTTPS deployment also configure DJANGO_DEBUG=false,
DJANGO_SECRET_KEY, DJANGO_ALLOWED_HOSTS, and DJANGO_CSRF_TRUSTED_ORIGINS.
Set DJANGO_TRUST_PROXY=true only behind a proxy that strips/replaces untrusted
forwarding headers. Secure session and CSRF cookies are enabled outside DEBUG.
Email delivery failures show actionable form feedback without leaving a new
registration activated. No SMTP credentials are bundled in source control.

## Local/ngrok launch

```powershell
$env:DJANGO_ALLOWED_HOSTS='127.0.0.1,localhost,diagnosis-catalyst-skydiver.ngrok-free.dev'
$env:DJANGO_CSRF_TRUSTED_ORIGINS='https://diagnosis-catalyst-skydiver.ngrok-free.dev'
$env:ACCOUNT_PUBLIC_ORIGIN='https://diagnosis-catalyst-skydiver.ngrok-free.dev'
.\env\Scripts\python.exe -B manage.py migrate
.\env\Scripts\python.exe -B manage.py runserver 127.0.0.1:8001 --noreload
```

Update the tunnel hostname if it changes. For local-only browsing unset
ACCOUNT_PUBLIC_ORIGIN so messages use the current local request origin.

## Validation

`python manage.py test accounts` covers the lifecycle, expiry, reused links,
CSRF, mail failure rollback, generic recovery, throttling, and session revocation.
`python manage.py test` also exercises existing catalog, cart, and checkout flows.
