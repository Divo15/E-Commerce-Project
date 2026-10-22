from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods

from carts.models import CartItem
from carts.services import get_cart, validate_stock

from .forms import ShippingDetailsForm
from .models import Order, OrderItem


def _pending_order(request, cart, lock=False):
    orders = Order.objects.filter(
        cart=cart,
        status=Order.PaymentStatus.PENDING,
        paid_at__isnull=True,
        stripe_checkout_session_id__isnull=True,
        stripe_payment_intent_id='',
    )
    if request.user.is_authenticated:
        orders = orders.filter(user=request.user)
    else:
        orders = orders.filter(pk=request.session.get('checkout_order_id'), user__isnull=True)
    if lock:
        orders = orders.select_for_update()
    # A signed-in customer can recover the latest draft on any device.
    return orders.order_by('-created_at', '-pk').first()


@never_cache
@require_http_methods(['GET', 'POST'])
@transaction.atomic
def shipping_details(request):
    cart = get_cart(request, lock=request.method == 'POST')
    cart_items = list(CartItem.objects.filter(
        cart=cart,
        is_active=True,
    ).select_related('product').order_by('pk')) if cart else []
    if not cart_items:
        messages.error(request, 'Add an item to your bag before entering shipping details.')
        return redirect('cart')
    order = _pending_order(request, cart, lock=request.method == 'POST')
    initial = {}
    if order is None:
        initial['shipping_country'] = 'India'
        if request.user.is_authenticated:
            initial.update({
                'shipping_name': f'{request.user.first_name} {request.user.last_name}'.strip(),
                'shipping_email': request.user.email,
                'shipping_phone': request.user.phone_number,
            })
    form = ShippingDetailsForm(
        request.POST if request.method == 'POST' else None,
        instance=order,
        initial=initial,
    )
    if request.method == 'POST' and form.is_valid():
        for item in cart_items:
            try:
                validate_stock(item.product, item.size, item.quantity)
                if item.quantity < 1 or item.product.price < 0:
                    raise ValidationError('This item needs to be updated in your bag.')
            except ValidationError as error:
                form.add_error(None, f'{item.product.product_name}: {" ".join(error.messages)}')
        total = sum(item.subtotal for item in cart_items)
        if total > 2147483647:
            form.add_error(None, 'Your bag total is too large. Please reduce the quantity.')
        if not form.errors:
            order = form.save(commit=False)
            order.cart = cart
            order.user = request.user if request.user.is_authenticated else None
            order.total_amount = total
            order.save()
            order.items.all().delete()
            OrderItem.objects.bulk_create([
                OrderItem(
                    order=order,
                    product=item.product,
                    product_name=item.product.product_name,
                    size=item.size,
                    unit_price=item.product.price,
                    quantity=item.quantity,
                )
                for item in cart_items
            ])
            request.session['checkout_order_id'] = order.pk
            return redirect('orders:shipping_review')
    return render(request, 'orders/shipping_details.html', {
        'form': form,
        'contact_fields': [form[name] for name in ('shipping_name', 'shipping_email', 'shipping_phone')],
        'address_fields': [form[name] for name in (
            'shipping_address_line1', 'shipping_address_line2', 'shipping_city',
            'shipping_state', 'shipping_postal_code', 'shipping_country',
            'shipping_landmark', 'shipping_instructions',
        )],
        'cart_items': cart_items,
        'quantity': sum(item.quantity for item in cart_items),
        'total': sum(item.subtotal for item in cart_items),
    })


@never_cache
@require_GET
def shipping_review(request):
    cart = get_cart(request)
    order = _pending_order(request, cart) if cart else None
    if order is None:
        return redirect('orders:shipping_details')
    saved_items = sorted(order.items.values_list('product_id', 'size', 'quantity', 'unit_price'))
    current_items = sorted(
        (item.product_id, item.size, item.quantity, item.product.price)
        for item in CartItem.objects.filter(cart=cart, is_active=True).select_related('product')
    )
    if current_items != saved_items:
        messages.warning(request, 'Your bag changed. Save shipping details again to refresh the review.')
        return redirect('orders:shipping_details')
    return render(request, 'orders/shipping_review.html', {
        'order': order,
        'order_items': order.items.all().order_by('pk'),
    })
