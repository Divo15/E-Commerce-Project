from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from store.models import Product

from .forms import AddCartForm, CartQuantityForm
from .models import Cart, CartItem
from .services import validate_stock


def _cart_id(request):
    cart_id = request.session.session_key
    if not cart_id:
        request.session.create()
        cart_id = request.session.session_key
    return cart_id


def _form_error(request, form):
    messages.error(request, ' '.join(
        error for errors in form.errors.values() for error in errors
    ))


@require_POST
def add_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_available=True)
    form = AddCartForm(request.POST, product=product)
    if not form.is_valid():
        _form_error(request, form)
        return redirect('cart')
    cart_id = _cart_id(request)
    try:
        with transaction.atomic():
            cart, _ = Cart.objects.get_or_create(cart_id=cart_id)
            cart = Cart.objects.select_for_update().get(pk=cart.pk)
            item = CartItem.objects.filter(
                cart=cart,
                product=product,
                size=form.cleaned_data['size'],
            ).first()
            quantity = form.cleaned_data['quantity']
            if item and item.is_active:
                quantity += item.quantity
            validate_stock(product, form.cleaned_data['size'], quantity)
            if item:
                item.quantity = quantity
                item.is_active = True
                item.save(update_fields=['quantity', 'is_active'])
            else:
                CartItem.objects.create(
                    cart=cart,
                    product=product,
                    size=form.cleaned_data['size'],
                    quantity=quantity,
                )
    except ValidationError as error:
        messages.error(request, ' '.join(error.messages))
    return redirect('cart')


def _update_cart_item(request, item_id, delta=None):
    with transaction.atomic():
        cart = get_object_or_404(
            Cart.objects.select_for_update(),
            cart_id=request.session.session_key,
        )
        item = get_object_or_404(
            CartItem.objects.select_related('product'),
            pk=item_id,
            cart=cart,
            is_active=True,
        )
        if delta is None:
            form = CartQuantityForm(request.POST)
            if not form.is_valid():
                _form_error(request, form)
                return redirect('cart')
            quantity = form.cleaned_data['quantity']
        else:
            quantity = item.quantity + delta
        if quantity == 0:
            item.delete()
        else:
            try:
                validate_stock(item.product, item.size, quantity)
            except ValidationError as error:
                messages.error(request, ' '.join(error.messages))
            else:
                item.quantity = quantity
                item.save(update_fields=['quantity'])
    return redirect('cart')


@require_POST
def update_cart(request, item_id):
    return _update_cart_item(request, item_id)


@require_POST
def increase_cart(request, item_id):
    return _update_cart_item(request, item_id, delta=1)


@require_POST
def decrease_cart(request, item_id):
    return _update_cart_item(request, item_id, delta=-1)


@require_POST
def remove_cart(request, item_id):
    item = get_object_or_404(
        CartItem,
        pk=item_id,
        cart__cart_id=request.session.session_key,
    )
    item.delete()
    return redirect('cart')


def cart(request):
    cart_items = list(CartItem.objects.filter(
        cart__cart_id=request.session.session_key,
        is_active=True,
    ).select_related('product__category__department').prefetch_related('product__inventory').order_by('pk'))
    for item in cart_items:
        item.product_url = (
            item.product.get_url()
            if item.product.is_available and item.product.category.department_id else ''
        )
        size_form = AddCartForm({'size': item.size}, product=item.product)
        valid_size = size_form.is_valid() and size_form.cleaned_data['size'] == item.size
        inventory = next((row for row in item.product.inventory.all() if row.size == item.size), None)
        item.available_quantity = inventory.quantity if inventory and valid_size and item.product.is_available else 0
        item.stock_message = ''
        if not valid_size:
            item.stock_message = 'Please remove this item and add it again with a valid size.'
        elif not item.product.is_available:
            item.stock_message = 'This product is no longer available.'
        elif item.available_quantity == 0:
            item.stock_message = 'This size is out of stock. Please remove this item.'
        elif item.quantity > item.available_quantity:
            item.stock_message = f'Only {item.available_quantity} item(s) are available. Please update the quantity.'
    return render(request, 'carts/cart.html', {
        'total': sum(item.subtotal for item in cart_items),
        'quantity': sum(item.quantity for item in cart_items),
        'cart_items': cart_items,
        'has_stock_issues': any(item.stock_message for item in cart_items),
    })
