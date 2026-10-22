# Saved shopping bags

The cart owner is now `Cart.user`, a nullable one-to-one account relationship.
`cart_id` remains unique for guest session compatibility, but it does not
authorize access to an account-owned bag. All bag reads, mutations, counters,
shipping, and review use the shared `carts.services.get_cart` resolver.

Guests resolve only unowned carts matching their current session. Signed-in
customers resolve only their own cart. Merely browsing never creates an empty
guest cart or session. Account-cart creation and guest merging lock the account
and affected carts to prevent duplicate ownership and repeated merges.

On login, matching active product/size rows combine quantities. Inactive target
rows are reactivated with the guest quantity, not their old quantity. Different
sizes remain separate. Stock is checked when adding/updating and during shipping;
over-stock merges remain visible so the customer can correct them.

Guest orders with no account owner are attached to the same customer and moved
to the surviving cart before retiring the guest cart. Account drafts are scoped
to both account and cart, and must remain pending, unpaid, and without payment
references. Review compares product/size/quantity/price snapshots to current bag
contents. Other customers' session pointers cannot grant access to these drafts.

Migration: `carts.0003_cart_user`. Existing guest carts and items remain intact.
No users or merchandise are created. Existing authenticated session carts are
claimed lazily on access or logout. A database backup is created before applying
the local migration under the ignored `.local/backups` directory.

Regression coverage in `carts/test_persistence.py` exercises logout/re-login,
new browsers, two devices, duplicate/size merging, other-user mutation attempts,
stock conflicts, draft recovery, changed review contents, and password change.
