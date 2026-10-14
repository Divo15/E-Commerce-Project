import re

from django import forms

from .models import Order


class ShippingDetailsForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = (
            'shipping_name', 'shipping_email', 'shipping_phone',
            'shipping_address_line1', 'shipping_address_line2',
            'shipping_city', 'shipping_state', 'shipping_postal_code',
            'shipping_country', 'shipping_landmark', 'shipping_instructions',
        )
        labels = {
            'shipping_name': 'Recipient full name',
            'shipping_email': 'Email address',
            'shipping_phone': 'Phone number',
            'shipping_address_line1': 'House / flat number and street',
            'shipping_address_line2': 'Area / locality (optional)',
            'shipping_city': 'City',
            'shipping_state': 'State / province',
            'shipping_postal_code': 'PIN / postal code',
            'shipping_country': 'Country',
            'shipping_landmark': 'Landmark (optional)',
            'shipping_instructions': 'Delivery instructions (optional)',
        }
        widgets = {
            'shipping_phone': forms.TextInput(attrs={'type': 'tel'}),
            'shipping_instructions': forms.Textarea(attrs={'rows': 3}),
        }
        help_texts = {
            'shipping_email': 'For updates about this order.',
            'shipping_phone': 'Include the country code for international numbers.',
            'shipping_postal_code': 'For India, enter your six-digit PIN code.',
            'shipping_instructions': 'Add any directions that will help the delivery person.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        optional_fields = {
            'shipping_address_line2', 'shipping_landmark', 'shipping_instructions',
        }
        autocomplete = {
            'shipping_name': 'shipping name',
            'shipping_email': 'shipping email',
            'shipping_phone': 'shipping tel',
            'shipping_address_line1': 'shipping address-line1',
            'shipping_address_line2': 'shipping address-line2',
            'shipping_city': 'shipping address-level2',
            'shipping_state': 'shipping address-level1',
            'shipping_postal_code': 'shipping postal-code',
            'shipping_country': 'shipping country-name',
        }
        for name, field in self.fields.items():
            field.required = name not in optional_fields
            field.widget.attrs['class'] = 'shipping-input'
            if name in autocomplete:
                field.widget.attrs['autocomplete'] = autocomplete[name]

    def clean_shipping_phone(self):
        phone = self.cleaned_data['shipping_phone']
        digits = re.sub(r'\D', '', phone)
        if not re.fullmatch(r'\+?[0-9 ()-]+', phone) or not 7 <= len(digits) <= 15:
            raise forms.ValidationError('Enter a valid phone number with 7 to 15 digits.')
        return phone

    def clean_shipping_country(self):
        country = self.cleaned_data['shipping_country']
        return 'India' if country.casefold() in {'india', 'in'} else country

    def clean(self):
        cleaned_data = super().clean()
        postal_code = cleaned_data.get('shipping_postal_code')
        country = cleaned_data.get('shipping_country')
        if postal_code:
            if country == 'India' and not re.fullmatch(r'[1-9][0-9]{5}', postal_code):
                self.add_error('shipping_postal_code', 'Enter a valid six-digit Indian PIN code.')
            elif not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9 -]*', postal_code):
                self.add_error('shipping_postal_code', 'Use letters, numbers, spaces, or hyphens for the postal code.')
        return cleaned_data
