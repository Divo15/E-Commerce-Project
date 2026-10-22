from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch, Mock
import json
import time

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from google.auth import crypt, jwt

from django.test import Client, TestCase, override_settings
from django.urls import reverse

from carts.models import Cart, CartItem
from category.models import Category, Department
from store.models import Product, ProductInventory
from .models import Account


@override_settings(GOOGLE_CLIENT_ID='test-client', GOOGLE_CLIENT_SECRET='test-secret', GOOGLE_OAUTH_CONFIG_FILE='missing-test-config.json', PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class GoogleSigninTests(TestCase):
    def start(self, client=None, **data):
        client = client or self.client
        response = client.post(reverse('accounts:google_start'), data)
        self.assertEqual(response.status_code, 302)
        return client.session['google_signin']

    def finish(self, attempt, claims=None, client=None):
        identity = {'sub': 'google-user-1', 'email': 'meera@gmail.com', 'email_verified': True, 'given_name': 'Meera', 'family_name': 'Rao', 'nonce': attempt['nonce']}
        identity.update(claims or {})
        token_response = Mock()
        token_response.json.return_value = {'id_token': 'signed-token'}
        with patch('accounts.google_auth.requests.post', return_value=token_response) as exchange, patch('accounts.google_auth.verify_oauth2_token', return_value=identity) as verify:
            response = (client or self.client).get(reverse('accounts:google_callback'), {'state': attempt['state'], 'code': 'one-time-code'})
            self.assertEqual(exchange.call_args.kwargs['data']['code_verifier'], attempt['verifier'])
            self.assertEqual(verify.call_args.kwargs['audience'], 'test-client')
            return response

    def existing(self, email='meera@gmail.com', **changes):
        user = Account.objects.create_user('Meera', 'Rao', 'meera', email, 'Velvet-forest-43!')
        user.is_active = True
        for key, value in changes.items():
            setattr(user, key, value)
        user.save()
        return user

    def signed_finish(self, attempt, claims=None, different_key=False):
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        trusted_key = rsa.generate_private_key(public_exponent=65537, key_size=2048) if different_key else key
        signer = crypt.RSASigner(key, key_id='test-key')
        public_key = trusted_key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()
        now = int(time.time())
        identity = {'iss': 'https://accounts.google.com', 'aud': 'test-client', 'sub': 'google-user-1', 'email': 'meera@gmail.com', 'email_verified': True, 'given_name': 'Meera', 'family_name': 'Rao', 'nonce': attempt['nonce'], 'iat': now + 2, 'exp': now + 3600}
        identity.update(claims or {})
        token_response = Mock()
        token_response.json.return_value = {'id_token': jwt.encode(signer, identity)}
        certificate_response = Mock(status=200, data=json.dumps({'test-key': public_key}).encode())
        with patch('accounts.google_auth.requests.post', return_value=token_response), patch('accounts.google_auth.google_request', return_value=certificate_response):
            return self.client.get(reverse('accounts:google_callback'), {'state': attempt['state'], 'code': 'one-time-code'})

    def test_real_verifier_accepts_a_signed_token_with_small_clock_difference(self):
        response = self.signed_finish(self.start())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session['_auth_user_id'], str(Account.objects.get().pk))

    def test_real_verifier_still_rejects_invalid_identity_and_tokens_outside_tolerance(self):
        now = int(time.time())
        for claims in [{'iat': now + 120}, {'iat': now - 4000, 'exp': now - 120}, {'aud': 'another-client'}, {'iss': 'https://example.com'}, {'nonce': 'wrong'}]:
            with self.subTest(claims=claims):
                self.assertEqual(self.signed_finish(self.start(), claims).status_code, 400)
                self.assertNotIn('_auth_user_id', self.client.session)
                self.assertFalse(Account.objects.exists())
        self.assertEqual(self.signed_finish(self.start(), different_key=True).status_code, 400)
        self.assertFalse(Account.objects.exists())

    def test_failure_diagnostics_do_not_log_codes_credentials_or_exception_details(self):
        attempt = self.start()
        with self.assertLogs('accounts.google_auth', level='WARNING') as logs, patch('accounts.google_auth.requests.post', side_effect=__import__('requests').exceptions.Timeout('private-code private-secret private@example.com')):
            response = self.client.get(reverse('accounts:google_callback'), {'state': attempt['state'], 'code': 'private-code'})
        self.assertEqual(response.status_code, 400)
        diagnostic = '\n'.join(logs.output)
        self.assertIn('stage=token_exchange', diagnostic)
        self.assertIn('error_type=Timeout', diagnostic)
        for sensitive in ['private-code', 'private-secret', 'private@example.com', attempt['state'], attempt['verifier']]:
            self.assertNotIn(sensitive, diagnostic)

    def test_start_uses_state_nonce_pkce_and_minimal_scopes(self):
        response = self.client.post(reverse('accounts:google_start'), {'next': 'https://example.com'})
        parts = urlsplit(response.url)
        params = parse_qs(parts.query)
        self.assertEqual(parts.netloc, 'accounts.google.com')
        self.assertEqual(params['scope'], ['openid email profile'])
        self.assertEqual(params['code_challenge_method'], ['S256'])
        self.assertTrue(params['nonce'][0])
        self.assertNotIn('test-secret', response.url)
        self.assertEqual(self.client.session['google_signin']['next'], reverse('accounts:account'))
        self.assertEqual(self.client.get(reverse('accounts:google_start')).status_code, 405)
        self.assertEqual(Client(enforce_csrf_checks=True).post(reverse('accounts:google_start')).status_code, 403)

    def test_new_customer_is_active_no_password_no_verification_email_and_profile_required(self):
        response = self.finish(self.start(next='/carts/'))
        self.assertEqual(urlsplit(response.url).path, reverse('accounts:details'))
        user = Account.objects.get()
        self.assertTrue(user.is_active)
        self.assertFalse(user.has_usable_password())
        self.assertFalse(user.email_verification_pending)
        self.assertIsNotNone(user.email_verified_at)
        self.assertEqual(user.google_subject, 'google-user-1')
        self.assertEqual(self.client.session['_auth_user_id'], str(user.pk))
        response = self.client.post(reverse('accounts:details'), {'first_name': 'Meera', 'last_name': 'Rao', 'phone_number': '9876543210', 'city': 'Chennai', 'postal_code': '600001', 'next': '/carts/'})
        self.assertRedirects(response, '/carts/')
        self.client.post(reverse('accounts:logout'))
        fresh = Client()
        self.assertRedirects(self.finish(self.start(fresh), client=fresh), reverse('accounts:account'))
        self.assertEqual(Account.objects.count(), 1)

    def test_guest_bag_is_attached_on_google_login(self):
        department = Department.objects.create(department_name='Women', slug='women')
        category = Category.objects.create(category_name='Sarees', slug='sarees', department=department)
        product = Product.objects.create(product_name='Saree', slug='saree', category=category, price=1000, color='Red')
        ProductInventory.objects.create(product=product, size='free_size', quantity=5)
        self.client.post(reverse('add_cart', args=[product.pk]), {'quantity': 2})
        self.finish(self.start())
        self.assertEqual(Cart.objects.get().user, Account.objects.get())
        self.assertEqual(CartItem.objects.get().quantity, 2)

    def test_bad_state_expiry_and_replay_never_exchange_code(self):
        attempt = self.start()
        url = reverse('accounts:google_callback')
        with patch('accounts.google_auth.requests.post') as exchange:
            self.assertEqual(self.client.get(url, {'state': 'wrong', 'code': 'bad'}).status_code, 400)
            self.assertEqual(self.client.get(url, {'state': attempt['state'], 'code': 'bad'}).status_code, 400)
            exchange.assert_not_called()
        attempt = self.start()
        session = self.client.session
        session['google_signin'] = {**attempt, 'started': 0}
        session.save()
        self.assertEqual(self.client.get(url, {'state': attempt['state'], 'code': 'bad'}).status_code, 400)

    def test_bad_nonce_and_unverified_email_do_not_log_in(self):
        for claims in [{'nonce': 'wrong'}, {'email_verified': False}, {'sub': ''}]:
            self.assertEqual(self.finish(self.start(), claims).status_code, 400)
            self.assertFalse(Account.objects.exists())
            self.assertNotIn('_auth_user_id', self.client.session)

    def test_google_cancellation_is_recoverable(self):
        attempt = self.start()
        response = self.client.get(reverse('accounts:google_callback'), {'state': attempt['state'], 'error': 'access_denied'})
        self.assertContains(response, 'cancelled', status_code=400)

    def test_existing_gmail_account_links_without_losing_details_or_password(self):
        user = self.existing(phone_number='9876543210', city='Chennai', postal_code='600001')
        self.assertRedirects(self.finish(self.start()), reverse('accounts:account'))
        user.refresh_from_db()
        self.assertEqual(user.google_subject, 'google-user-1')
        self.assertTrue(user.has_usable_password())
        self.assertEqual(user.city, 'Chennai')
        self.assertEqual(Account.objects.count(), 1)

    def test_unverified_signup_password_is_discarded_when_google_verifies_owner(self):
        user = self.existing(is_active=False, email_verification_pending=True)
        self.finish(self.start())
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertFalse(user.has_usable_password())

    def test_disabled_accounts_and_conflicting_identity_are_rejected(self):
        user = self.existing(is_active=False)
        self.assertEqual(self.finish(self.start()).status_code, 400)
        user.is_active = True
        user.google_subject = 'different-google-user'
        user.save()
        self.assertEqual(self.finish(self.start()).status_code, 400)

    def test_existing_third_party_email_requires_authenticated_linking(self):
        user = self.existing(email='meera@example.com')
        self.assertEqual(self.finish(self.start(), {'email': user.email}).status_code, 400)
        user.refresh_from_db()
        self.assertIsNone(user.google_subject)
        self.client.force_login(user)
        self.finish(self.start(), {'email': user.email})
        user.refresh_from_db()
        self.assertEqual(user.google_subject, 'google-user-1')

    @override_settings(GOOGLE_CLIENT_ID='', GOOGLE_CLIENT_SECRET='')
    def test_unconfigured_button_is_disabled_and_start_is_honest(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertContains(response, 'disabled aria-describedby="google-setup-note"')
        self.assertEqual(self.client.post(reverse('accounts:google_start')).status_code, 503)

    def test_invalid_signature_or_google_unavailable_does_not_authenticate(self):
        attempt = self.start()
        with patch('accounts.google_auth.requests.post', side_effect=__import__('requests').exceptions.Timeout):
            self.assertEqual(self.client.get(reverse('accounts:google_callback'), {'state': attempt['state'], 'code': 'code'}).status_code, 400)
        self.assertFalse(Account.objects.exists())
        attempt = self.start()
        token_response = Mock()
        token_response.json.return_value = {'id_token': 'invalid-token'}
        with patch('accounts.google_auth.requests.post', return_value=token_response), patch('accounts.google_auth.verify_oauth2_token', side_effect=ValueError('Invalid signature')):
            self.assertEqual(self.client.get(reverse('accounts:google_callback'), {'state': attempt['state'], 'code': 'code'}).status_code, 400)
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertFalse(Account.objects.exists())

    @override_settings(ACCOUNT_PUBLIC_ORIGIN='https://diagnosis-catalyst-skydiver.ngrok-free.dev', ALLOWED_HOSTS=['diagnosis-catalyst-skydiver.ngrok-free.dev'])
    def test_ngrok_uses_https_callback_uri(self):
        self.client.post(reverse('accounts:google_start'), HTTP_HOST='diagnosis-catalyst-skydiver.ngrok-free.dev')
        self.assertEqual(self.client.session['google_signin']['redirect_uri'], 'https://diagnosis-catalyst-skydiver.ngrok-free.dev/accounts/google/callback/')
