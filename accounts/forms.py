from django import forms
from django.contrib.auth.password_validation import validate_password

from .models import Account
import re
from uuid import uuid4


def clean_phone(value):
    if not re.fullmatch(r'\+?[0-9 ()-]+', value) or not 7 <= len(re.sub(r'\D', '', value)) <= 15:
        raise forms.ValidationError('Enter a valid phone number with 7 to 15 digits.')
    return value


class CustomerDetailsForm(forms.ModelForm):
    postal_code = forms.RegexField(regex=r'^[0-9]{6}$', label='PIN / postal code', error_messages={'invalid': 'Enter a valid 6-digit PIN or postal code.'})

    class Meta:
        model = Account
        fields = ('first_name', 'last_name', 'phone_number', 'city', 'postal_code')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.required = True
            field.widget.attrs['class'] = 'commerce-input'
            field.widget.attrs['autocomplete'] = {'first_name': 'given-name', 'last_name': 'family-name', 'phone_number': 'tel', 'city': 'address-level2', 'postal_code': 'postal-code'}[name]
        self.fields['postal_code'].widget.attrs.update({'inputmode': 'numeric', 'maxlength': '6'})

    def clean_phone_number(self):
        return clean_phone(self.cleaned_data['phone_number'])


class RegistrationForm(forms.ModelForm):
    def clean_phone_number(self):
        return clean_phone(self.cleaned_data['phone_number'])

    city = forms.CharField(max_length=100, label='City')
    postal_code = forms.RegexField(
        regex=r'^[0-9]{6}$',
        label='PIN / postal code',
        help_text='Enter your 6-digit PIN or postal code.',
        error_messages={'invalid': 'Enter a valid 6-digit PIN or postal code.'},
    )
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Account
        fields = (
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'city',
            'postal_code',
        )

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if Account.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        autocomplete = {
            'first_name': 'given-name', 'last_name': 'family-name',
            'email': 'email', 'phone_number': 'tel',
            'password': 'new-password', 'confirm_password': 'new-password',
            'city': 'address-level2', 'postal_code': 'postal-code',
        }
        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'commerce-input', 'autocomplete': autocomplete[name]})
        self.fields['phone_number'].widget.attrs['type'] = 'tel'
        self.fields['postal_code'].widget.attrs.update({'inputmode': 'numeric', 'pattern': '[0-9]{6}', 'maxlength': '6'})
        self.fields['password'].help_text = 'Use at least 8 characters. Avoid common or entirely numeric passwords.'

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password:
            candidate = Account(**{name: cleaned_data.get(name, '') for name in ('first_name', 'last_name', 'email')})
            validate_password(password, user=candidate)

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Passwords do not match.')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        if not user.username:
            user.username = f'customer_{uuid4().hex}'
        user.set_password(self.cleaned_data['password'])
        user.is_active = False
        user.email_verification_pending = True

        if commit:
            user.save()

        return user
