from django import forms
from django.contrib.auth.password_validation import validate_password

from .models import Account


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = Account
        fields = (
            'first_name',
            'last_name',
            'username',
            'email',
            'phone_number',
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
            'username': 'username', 'email': 'email', 'phone_number': 'tel',
            'password': 'new-password', 'confirm_password': 'new-password',
        }
        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'commerce-input', 'autocomplete': autocomplete[name]})
        self.fields['phone_number'].widget.attrs['type'] = 'tel'

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password:
            validate_password(password)

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Passwords do not match.')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.is_active = True

        if commit:
            user.save()

        return user
