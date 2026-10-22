import re
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from accounts.forms import CustomerDetailsForm
from carts.forms import AddCartForm
from carts.services import get_cart, validate_stock
from ecommerce.public_urls import public_url
from store.models import Product, ProductInventory


def one_line(value):
    return ' '.join(str(value).split())


def customer_gate(request, return_url):
    if not request.user.is_authenticated:
        return redirect_to_login(return_url)
    form = CustomerDetailsForm({name: getattr(request.user, name) for name in CustomerDetailsForm.Meta.fields}, instance=request.user)
    if not form.is_valid():
        messages.info(request, 'Please complete your contact details before ordering on WhatsApp.')
        return redirect(reverse('accounts:details') + '?' + urlencode({'next': return_url}))


def handoff(request, lines):
    number = re.sub(r'[+ ()-]', '', settings.WHATSAPP_ORDER_NUMBER)
    if not re.fullmatch(r'[1-9][0-9]{7,14}', number):
        messages.error(request, 'WhatsApp ordering is temporarily unavailable. Please try again later.')
        return redirect('cart')
    user = request.user
    contact = [
        'Customer details',
        f'Full name: {one_line(user.first_name)} {one_line(user.last_name)}',
        f'Email: {one_line(user.email)}',
        f'Phone: {one_line(user.phone_number)}',
        f'City: {one_line(user.city)}',
        f'PIN: {one_line(user.postal_code)}',
    ]
    text = '\n'.join(['Hello Shali Collections, I would like to buy:', '', *lines, '', *contact, '', 'Please confirm availability, delivery arrangements, and payment details.'])
    response = redirect(f'https://wa.me/{number}?' + urlencode({'text': text}))
    response['Referrer-Policy'] = 'no-referrer'
    return response


def product_lines(request, product, size, quantity):
    link = public_url(request, product.get_url())
    label = dict(ProductInventory.Size.choices).get(size, size)
    lines = [one_line(product.product_name)]
    if size != 'no_size':
        lines.append(f'Size: {label}')
    lines.extend([f'Quantity: {quantity}', f'Unit price: ₹{product.price:,}', f'Subtotal: ₹{product.price * quantity:,}', link])
    if product.image_1:
        # Click-to-chat accepts text only; include an accessible photo URL.
        lines.append(f'Photo: {public_url(request, product.image_1.url)}')
    return lines


@never_cache
@require_POST
@transaction.atomic
def buy_now(request, product_id):
    product = get_object_or_404(Product.objects.select_related('category__department'), pk=product_id, is_available=True, category__department__isnull=False)
    form = AddCartForm(request.POST, product=product)
    if not form.is_valid():
        messages.error(request, 'Please select an available size and a valid quantity.')
        return redirect(product.get_url())
    return_url = product.get_url() + '?' + urlencode({'size': form.cleaned_data['size'], 'quantity': form.cleaned_data['quantity']})
    gate = customer_gate(request, return_url)
    if gate is not None:
        return gate
    try:
        validate_stock(product, form.cleaned_data['size'], form.cleaned_data['quantity'])
    except ValidationError as error:
        messages.error(request, ' '.join(error.messages))
        return redirect(product.get_url())
    return handoff(request, product_lines(request, product, form.cleaned_data['size'], form.cleaned_data['quantity']))


@never_cache
@require_POST
@transaction.atomic
def buy_bag(request):
    gate = customer_gate(request, reverse('cart'))
    if gate is not None:
        return gate
    cart = get_cart(request, lock=True)
    items = list(cart.items.filter(is_active=True).select_related('product__category__department').order_by('pk')) if cart else []
    if not items:
        messages.error(request, 'Add an item to your bag first.')
        return redirect('cart')
    lines = []
    for item in items:
        try:
            if not item.product.category.department_id:
                raise ValidationError('This product is no longer available.')
            validate_stock(item.product, item.size, item.quantity)
        except ValidationError as error:
            messages.error(request, f'{item.product.product_name}: {" ".join(error.messages)}')
            return redirect('cart')
        lines.extend([*product_lines(request, item.product, item.size, item.quantity), ''])
    lines.append(f'Item total: ₹{sum(item.subtotal for item in items):,}')
    return handoff(request, lines)
