from django.core.exceptions import ValidationError

from store.models import ProductInventory

from .forms import AddCartForm


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
