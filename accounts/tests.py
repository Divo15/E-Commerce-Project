from django.test import Client, TestCase
from django.urls import reverse

from carts.models import Cart, CartItem
from category.models import Category, Department
from orders.models import Order, OrderItem
from store.models import Product, ProductInventory

from .models import Account


class AccountFlowTests(TestCase):
    password = 'A-long-test-password-42'

    @classmethod
    def setUpTestData(cls):
        cls.user = Account.objects.create_user(
            first_name='Asha', last_name='Rao', username='asha',
            email='asha@example.com', password=cls.password,
        )
        cls.user.is_active = True
        cls.user.save()

    def test_login_page_has_live_fields_and_preserves_next(self):
        response = self.client.get(reverse('accounts:login'), {'next': reverse('cart')})
        self.assertTemplateUsed(response, 'base.html')
        for text in ['name="email"', 'name="password"', 'name="csrfmiddlewaretoken"', 'name="next" value="/carts/"']:
            self.assertContains(response, text)
        self.assertNotContains(response, 'text/babel')

    def test_login_rotates_session_without_losing_guest_bag_or_shipping_draft(self):
        department = Department.objects.create(department_name='Women', slug='women')
        category = Category.objects.create(category_name='Sarees', slug='sarees', department=department)
        product = Product.objects.create(product_name='Saree', slug='saree', category=category, price=1500, color='Red')
        ProductInventory.objects.create(product=product, size='free_size', quantity=3)
        self.client.post(reverse('add_cart', args=[product.pk]), {'quantity': 2})
        cart = Cart.objects.get()
        old_session_key = self.client.session.session_key
        order = Order.objects.create(cart=cart, total_amount=3000, shipping_name='Asha Rao')
        OrderItem.objects.create(
            order=order, product=product, product_name='Saree',
            unit_price=1500, quantity=2, size='free_size',
        )
        session = self.client.session
        session['checkout_order_id'] = order.pk
        session.save()
        response = self.client.post(reverse('accounts:login'), {
            'email': self.user.email, 'password': self.password, 'next': reverse('orders:shipping_review'),
        })
        self.assertRedirects(response, reverse('orders:shipping_review'))
        cart.refresh_from_db()
        self.assertNotEqual(cart.cart_id, old_session_key)
        self.assertEqual(cart.cart_id, self.client.session.session_key)
        self.assertEqual(CartItem.objects.get().quantity, 2)
        self.assertEqual(self.client.get(reverse('cart')).context['quantity'], 2)
        self.assertContains(self.client.get(reverse('home')), 'Shopping bag, 2 items')
        self.assertEqual(self.client.get(reverse('orders:shipping_review')).context['order'], order)

    def test_login_rejects_missing_wrong_and_inactive_credentials(self):
        for data in [{}, {'email': self.user.email}, {'email': self.user.email, 'password': 'wrong'}]:
            with self.subTest(data=data):
                response = self.client.post(reverse('accounts:login'), data)
                self.assertContains(response, 'role="alert"')
                self.assertNotIn('_auth_user_id', self.client.session)
        self.user.is_active = False
        self.user.save()
        response = self.client.post(reverse('accounts:login'), {'email': self.user.email, 'password': self.password})
        self.assertContains(response, 'Invalid email or password.')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_failed_login_retains_email_and_next_but_not_password(self):
        response = self.client.post(reverse('accounts:login'), {
            'email': ' asha@example.com ', 'password': 'wrong-secret', 'next': reverse('cart'),
        })
        self.assertContains(response, 'value="asha@example.com"')
        self.assertContains(response, 'name="next" value="/carts/"')
        self.assertNotContains(response, 'wrong-secret')

    def test_external_redirect_is_rejected(self):
        response = self.client.post(reverse('accounts:login'), {
            'email': self.user.email, 'password': self.password, 'next': 'https://example.com/',
        })
        self.assertRedirects(response, reverse('home'))

    def test_logout_requires_post_and_clears_authentication(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('accounts:logout')).status_code, 405)
        self.assertRedirects(self.client.post(reverse('accounts:logout')), reverse('accounts:login'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_account_mutations_require_csrf(self):
        client = Client(enforce_csrf_checks=True)
        for name in ['login', 'register', 'logout']:
            with self.subTest(name=name):
                self.assertEqual(client.post(reverse(f'accounts:{name}'), {}).status_code, 403)

    def test_registration_creates_active_account_with_hashed_password(self):
        response = self.client.post(reverse('accounts:register'), {
            'first_name': 'Meera', 'last_name': 'Rao', 'username': 'meera',
            'email': 'MEERA@example.com', 'phone_number': '9876543210',
            'password': self.password, 'confirm_password': self.password,
        })
        self.assertRedirects(response, reverse('accounts:login'))
        user = Account.objects.get(username='meera')
        self.assertEqual(user.email, 'meera@example.com')
        self.assertTrue(user.is_active)
        self.assertTrue(user.check_password(self.password))
        self.assertFalse(user.is_admin)

    def test_empty_registration_post_displays_required_errors(self):
        response = self.client.post(reverse('accounts:register'), {})
        self.assertTemplateUsed(response, 'base.html')
        self.assertContains(response, 'Check the details below.')
        self.assertTrue(response.context['form'].is_bound)
        self.assertEqual(Account.objects.count(), 1)

    def test_duplicate_email_and_password_mismatch_do_not_create_account(self):
        data = {
            'first_name': 'Meera', 'last_name': 'Rao', 'username': 'meera',
            'email': 'ASHA@example.com', 'phone_number': '9876543210',
            'password': self.password, 'confirm_password': 'different-password',
        }
        response = self.client.post(reverse('accounts:register'), data)
        self.assertIn('email', response.context['form'].errors)
        self.assertIn('confirm_password', response.context['form'].errors)
        self.assertEqual(Account.objects.count(), 1)
