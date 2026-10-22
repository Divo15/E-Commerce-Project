from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.db import transaction
from uuid import uuid4

from store.models import ProductInventory

from .forms import AddCartForm
from .models import Cart, CartItem


@transaction.atomic
def merge_guest_cart(user, guest_key, session_key):
    # Serialize sign-ins/mutations for a customer, including first-cart creation.
    get_user_model().objects.select_for_update().get(pk=user.pk)
    saved = Cart.objects.select_for_update().filter(user=user).first()
    guest = Cart.objects.select_for_update().filter(user__isnull=True, cart_id=guest_key).first() if guest_key else None
    if not guest:
        return saved
    if saved is None:
        guest.user = user
        guest.cart_id = session_key or f'account:{uuid4()}'
        guest.save(update_fields=['user', 'cart_id'])
        saved = guest
    else:
        for item in guest.items.filter(is_active=True).order_by('pk'):
            current = saved.items.filter(product=item.product, size=item.size).first()
            if current:
                current.quantity = current.quantity + item.quantity if current.is_active else item.quantity
                current.is_active = True
                current.save(update_fields=['quantity', 'is_active'])
                item.delete()
            else:
                item.cart = saved
                item.save(update_fields=['cart'])
        # Preserve order history as well as drafts before retiring the guest bag.
        guest.orders.filter(user__isnull=True).update(user=user, cart=saved)
        guest.delete()
    saved.orders.filter(user__isnull=True).update(user=user)
    return saved


def get_cart(request, *, create=False, lock=False):
    if request.user.is_authenticated:
        # Adopt legacy session bags on their first authenticated visit.
        if request.session.session_key and Cart.objects.filter(cart_id=request.session.session_key, user__isnull=True).exists():
            merge_guest_cart(request.user, request.session.session_key, request.session.session_key)
        carts = Cart.objects.filter(user=request.user)
        if create:
            with transaction.atomic():
                get_user_model().objects.select_for_update().get(pk=request.user.pk)
                cart, _ = Cart.objects.get_or_create(user=request.user, defaults={'cart_id': f'account:{uuid4()}'})
        else:
            cart = carts.first()
    else:
        key = request.session.session_key
        if create and not key:
            request.session.create()
            key = request.session.session_key
        carts = Cart.objects.filter(user__isnull=True, cart_id=key) if key else Cart.objects.none()
        if create:
            cart, _ = Cart.objects.get_or_create(user=None, cart_id=key)
        else:
            cart = carts.first()
    if cart and lock:
        cart = Cart.objects.select_for_update().get(pk=cart.pk)
    return cart


def validate_stock(product, size, quantity):
    if not product.is_available:
        raise ValidationError('This product is no longer available.')
    size_form = AddCartForm({'size': size}, product=product)
    if not size_form.is_valid() or size_form.cleaned_data['size'] != size:
        raise ValidationError('Please remove this item and add it again with a valid size.')
    inventory = ProductInventory.objects.select_for_update().filter(
        product=product,
        size=size,
    ).first()
    if inventory is None or inventory.quantity == 0:
        raise ValidationError('This product is out of stock in the selected size.')
    if quantity > inventory.quantity:
        raise ValidationError(f'Only {inventory.quantity} item(s) are available in the selected size.')
