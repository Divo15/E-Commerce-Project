from django import forms

from store.models import Product, ProductInventory


class AddCartForm(forms.Form):
    size = forms.ChoiceField(required=False)
    quantity = forms.IntegerField(required=False, min_value=1, max_value=2147483647)

    def __init__(self, *args, product, **kwargs):
        super().__init__(*args, **kwargs)
        self.product = product
        allowed_sizes = {
            Product.SizeType.CLOTHING: (
                ProductInventory.Size.S,
                ProductInventory.Size.XL,
                ProductInventory.Size.XXL,
            ),
            Product.SizeType.FREE_SIZE: (ProductInventory.Size.FREE_SIZE,),
            Product.SizeType.NO_SIZE: (ProductInventory.Size.NO_SIZE,),
        }
        self.fields['size'].choices = [
            (size, size.label) for size in allowed_sizes[product.size_type]
        ]
        self.fields['size'].required = product.size_type == Product.SizeType.CLOTHING

    def clean_size(self):
        size = self.cleaned_data['size']
        if not size:
            size = self.fields['size'].choices[0][0]
        return size

    def clean_quantity(self):
        return self.cleaned_data['quantity'] or 1


class CartQuantityForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, max_value=2147483647)
