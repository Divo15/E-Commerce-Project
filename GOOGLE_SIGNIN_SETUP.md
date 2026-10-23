# Connect Google sign-in

**Current status — 23 October 2026:** Existing Google Web client credentials are installed privately in Railway and local/ngrok login previously worked. Final www-domain callback registration, canonical public origin, audience/publishing and live sign-in checks remain. See [HANDOFF.md](HANDOFF.md) for verified deployment state. The setup below is a reference for maintaining the existing client, not an instruction to recreate it.

## Owner setup

1. Open [Google Auth Platform](https://console.cloud.google.com/auth/overview).
   Select or create a project for **Shali Collections**.
2. Configure Branding with the store name, support email, and developer contact.
   Set Audience to External. While the app is in Testing, add the Google accounts
   that will test sign-in under test users.
3. Under **Clients**, create an OAuth client of type **Web application**. Add
   these exact **Authorized redirect URIs** (including the final slash):

   ```text
   http://127.0.0.1:8001/accounts/google/callback/
   http://localhost:8001/accounts/google/callback/
   https://diagnosis-catalyst-skydiver.ngrok-free.dev/accounts/google/callback/
   https://e-commerce-project-production-6748.up.railway.app/accounts/google/callback/
   https://www.shalicollections.com/accounts/google/callback/
   ```

4. Download that client's JSON configuration. Save the downloaded file as:

   ```text
   D:\Backend\.local\google-oauth.json
   ```

   Keep the Google `web` wrapper in the downloaded JSON. This folder is ignored
   by Git and is not served as static content. Do not paste the client secret
   into chat, frontend code, screenshots, or the repository. The app reads this
   file at request time, so refreshing the sign-in page enables the button.

Alternatively set both GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in the server
environment and restart the app. Environment values override the private file.
No JavaScript-origin configuration is required for this server redirect flow.

When moving to a permanent domain, add its exact HTTPS callback URI in Google
and update ACCOUNT_PUBLIC_ORIGIN, DJANGO_ALLOWED_HOSTS, and
DJANGO_CSRF_TRUSTED_ORIGINS. Complete Google's publishing/branding requirements
before inviting all customers. Testing-mode credentials are not a public launch.

## Customer experience

Continue with Google opens Google's account chooser. The app requests only
openid, email, and profile. New customers get a store account with an unusable
local password; no store verification email is sent. Names come from Google.
Phone number, city, PIN, and missing name fields are collected once on the
contact-details screen. A saved product/size/quantity destination is restored
after completing these details. The customer's guest bag is attached or merged
into their saved account bag using the same persistence rules as email login.

Existing email/password sign-in remains available for existing customers. A
customer who uses Google-only sign-in returns through Google rather than the
store's password-reset or change-password forms.

## Identity and security behavior

- Authorization code exchange uses PKCE S256, session-bound state and nonce.
  Attempts expire after ten minutes and are consumed on callback.
- Google's official google-auth library verifies the ID token's signature,
  audience, issuer and expiry, with a maximum 30-second clock tolerance;
  the application additionally checks nonce and
  verified-email claims. Google subject (`sub`) is the stable identity key.
- Google passwords and access/refresh/ID tokens are not stored in the database.
- Existing Gmail/Workspace email matches can be linked when Google is
  authoritative for the address. Non-authoritative third-party email matches
  require signing in to the existing store account before linking from Account.
- Matching pending email registrations lose their previously unverified password
  before Google activates them, preventing an earlier signup from retaining access.
- Disabled accounts and conflicting Google identities cannot be reactivated or
  overwritten by the callback. New third-party Google email identities are tied
  to their subject, not a promise of current ownership of that email mailbox.
- Starts require a CSRF-protected POST and are rate limited. The callback rejects
  external return destinations and does not expose token-exchange diagnostics.

## Validation

`python manage.py test accounts.test_google` tests mocked success, returning
users, profile completion, bag preservation, invalid state/nonce, expired/reused
attempts, cancellation, disabled/conflicting accounts, safe linking, missing
configuration, provider timeouts, and the ngrok HTTPS callback URI.

The existing client's credentials are configured. Real Google sign-in on the final domain still needs callback/audience configuration and an end-to-end check; page-load tests alone do not establish that.

In local debug mode, callback failures write only the failing stage, a fixed
reason category and exception type to `.local/google-signin.log`. No OAuth
codes, credentials, identity tokens, email addresses or raw exception text are
logged by this diagnostic. Start a fresh sign-in after a failure; callback codes
are single-use and refreshing the failed callback cannot retry authentication.

References: [Google OIDC](https://developers.google.com/identity/openid-connect/openid-connect),
[Google ID-token verification](https://developers.google.com/identity/gsi/web/guides/verify-google-id-token).
