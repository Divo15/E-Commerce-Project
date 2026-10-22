import re
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .lifecycle import verification_tokens
from .models import Account
from .forms import RegistrationForm


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class AccountLifecycleTests(TestCase):
    password = 'Velvet-forest-river-43!'
    new_password = 'Golden-forest-river-87!'

    def test_signup_without_username_allows_customers_with_same_name(self):
        self.assertNotContains(self.client.get(reverse('accounts:register')), 'name="username"')
        for email in ['first@example.com', 'second@example.com']:
            form = RegistrationForm({
                'first_name': 'Meera', 'last_name': 'Rao', 'email': email,
                'phone_number': '9876543210', 'city': 'Chennai', 'postal_code': '600001',
                'password': self.password, 'confirm_password': self.password,
                'username': 'untrusted-value',
            })
            self.assertTrue(form.is_valid(), form.errors)
            user = form.save()
            self.assertNotEqual(user.username, 'untrusted-value')
        self.assertEqual(Account.objects.values('username').distinct().count(), 2)

    def registration(self):
        return self.client.post(reverse('accounts:register'), {
            'first_name': 'Meera', 'last_name': 'Rao',
            'email': 'MEERA@example.com', 'phone_number': '9876543210',
            'city': 'Chennai', 'postal_code': '600001',
            'password': self.password, 'confirm_password': self.password,
        })

    def active_user(self):
        user = Account.objects.create_user('Meera', 'Rao', 'meera', 'meera@example.com', self.password)
        user.is_active = True
        user.save()
        return user

    def verification_path(self, user):
        return reverse('accounts:verify_email', args=[urlsafe_base64_encode(force_bytes(user.pk)), verification_tokens.make_token(user)])

    def test_register_verify_login_account_logout(self):
        self.assertRedirects(self.registration(), reverse('accounts:verification_sent'))
        user = Account.objects.get(email='meera@example.com')
        self.assertFalse(user.is_active)
        self.assertEqual(len(mail.outbox), 1)
        link = re.search(r'https?://[^\s]+', mail.outbox[0].body).group()
        self.client.post(reverse('accounts:login'), {'email': user.email, 'password': self.password})
        self.assertNotIn('_auth_user_id', self.client.session)
        self.client.get(link)
        user.refresh_from_db()
        self.assertFalse(user.is_active)  # Mail scanners must not activate accounts.
        self.assertContains(self.client.post(link), 'Your email is verified')
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertIsNotNone(user.email_verified_at)
        self.assertEqual(self.client.post(link).status_code, 400)
        self.client.post(reverse('accounts:login'), {'email': 'MEERA@EXAMPLE.COM', 'password': self.password})
        self.assertIn('_auth_user_id', self.client.session)
        self.assertContains(self.client.get(reverse('accounts:account')), 'Sign out')
        self.assertRedirects(self.client.post(reverse('accounts:logout')), reverse('accounts:login'))
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertRedirects(self.client.get(reverse('accounts:account')), reverse('accounts:login') + '?next=/accounts/')

    def test_verification_expiry_tamper_and_disabled_account(self):
        self.registration()
        user = Account.objects.get(email='meera@example.com')
        path = self.verification_path(user)
        with patch.object(verification_tokens, '_now', return_value=verification_tokens._now() + timedelta(hours=2)):
            self.assertEqual(self.client.post(path).status_code, 400)
        self.assertEqual(self.client.post(path[:-1] + 'x/').status_code, 400)
        user.email_verification_pending = False
        user.save()
        self.client.post(reverse('accounts:resend_verification'), {'email': user.email})
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(self.client.post(path).status_code, 400)

    def test_resend_is_generic_and_throttled(self):
        for _ in range(5):
            response = self.client.post(reverse('accounts:resend_verification'), {'email': 'unknown@example.com'})
            self.assertContains(response, 'Email delivery is not connected')
        self.assertEqual(self.client.post(reverse('accounts:resend_verification'), {'email': 'unknown@example.com'}).status_code, 429)
        self.assertEqual(len(mail.outbox), 0)

    def test_reset_email_link_password_change_and_token_replay(self):
        user = self.active_user()
        old_client = Client()
        old_client.force_login(user)
        self.assertRedirects(self.client.post(reverse('accounts:password_reset'), {'email': user.email}), reverse('accounts:password_reset_done'))
        link = re.search(r'https?://[^\s]+', mail.outbox[0].body).group()
        response = self.client.get(link, follow=True)
        self.assertContains(response, 'Choose a new password')
        confirm_url = response.redirect_chain[-1][0]
        self.assertRedirects(self.client.post(confirm_url, {'new_password1': self.new_password, 'new_password2': self.new_password}), reverse('accounts:password_reset_complete'))
        user.refresh_from_db()
        self.assertTrue(user.check_password(self.new_password))
        self.assertFalse(user.check_password(self.password))
        self.assertContains(self.client.get(link, follow=True), 'This link is no longer valid')
        self.assertEqual(old_client.get(reverse('accounts:account')).status_code, 302)

    def test_unknown_and_unverified_reset_have_same_confirmation_and_no_mail(self):
        self.registration()
        mail.outbox.clear()
        for email in ['meera@example.com', 'unknown@example.com']:
            self.assertRedirects(self.client.post(reverse('accounts:password_reset'), {'email': email}), reverse('accounts:password_reset_done'))
        self.assertEqual(len(mail.outbox), 0)

    def test_change_password_keeps_current_session_and_revokes_other_sessions(self):
        user = self.active_user()
        self.client.force_login(user)
        other = Client()
        other.force_login(user)
        self.assertRedirects(self.client.post(reverse('accounts:password_change'), {'old_password': self.password, 'new_password1': self.new_password, 'new_password2': self.new_password}), reverse('accounts:password_change_done'))
        self.assertEqual(self.client.get(reverse('accounts:account')).status_code, 200)
        self.assertEqual(other.get(reverse('accounts:account')).status_code, 302)

    def test_verification_requires_csrf_and_registration_rolls_back_when_mail_fails(self):
        with patch('accounts.views.send_verification', side_effect=OSError('mail unavailable')):
            self.assertContains(self.registration(), 'We could not send the verification email')
        self.assertFalse(Account.objects.exists())
        self.registration()
        user = Account.objects.get(email='meera@example.com')
        self.assertEqual(Client(enforce_csrf_checks=True).post(self.verification_path(user)).status_code, 403)

    def test_reset_expired_link_and_bad_password_rejected(self):
        user = self.active_user()
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        link = reverse('accounts:password_reset_confirm', args=[uid, token])
        with patch.object(default_token_generator, '_now', return_value=default_token_generator._now() + timedelta(hours=2)):
            self.assertContains(self.client.get(link, follow=True), 'This link is no longer valid')
        response = self.client.get(link, follow=True)
        confirm = response.redirect_chain[-1][0]
        response = self.client.post(confirm, {'new_password1': '123', 'new_password2': '123'})
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.check_password(self.password))
