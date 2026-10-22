from django.test import Client, TestCase, override_settings
from django.urls import reverse

from accounts.models import Account
from category.models import Category, Department
from orders.models import Order, OrderItem
from store.models import Product, ProductInventory
from .models import Cart, CartItem


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class PersistentCartTests(TestCase):
    password = 'Velvet-forest-43!'

    def setUp(self):
        self.user = Account.objects.create_user('Asha', 'Rao', 'asha', 'asha@example.com', self.password)
        self.user.is_active = True
        self.user.save()
        self.other_user = Account.objects.create_user('Meera', 'Rao', 'meera', 'meera@example.com', self.password)
        self.other_user.is_active = True
        self.other_user.save()
        department = Department.objects.create(department_name='Women', slug='women')
        category = Category.objects.create(category_name='Dresses', slug='dresses', department=department)
        self.product = Product.objects.create(product_name='Dress', slug='dress', price=1000, color='Red', category=category, size_type='clothing')
        ProductInventory.objects.create(product=self.product, size='s', quantity=5)
        ProductInventory.objects.create(product=self.product, size='xl', quantity=5)

    def signin(self, client, user=None):
        return client.post(reverse('accounts:login'), {'email': (user or self.user).email, 'password': self.password})

    def add(self, client, size='s', quantity=1):
        return client.post(reverse('add_cart', args=[self.product.pk]), {'size': size, 'quantity': quantity})

    def test_logout_fresh_browser_and_other_device_restore_same_bag(self):
        self.add(self.client, quantity=2)
        self.signin(self.client)
        saved = Cart.objects.get(user=self.user)
        self.client.post(reverse('accounts:logout'))
        self.assertEqual(self.client.get(reverse('cart')).context['quantity'], 0)
        fresh = Client()
        self.signin(fresh)
        self.assertEqual(fresh.get(reverse('cart')).context['quantity'], 2)
        self.assertContains(fresh.get(reverse('home')), 'Shopping bag, 2 items')
        self.add(fresh, quantity=1)
        self.signin(self.client)
        self.assertEqual(self.client.get(reverse('cart')).context['quantity'], 3)
        self.assertEqual(Cart.objects.filter(user=self.user).count(), 1)
        self.assertEqual(saved.items.get().quantity, 3)

    def test_guest_merge_sums_duplicates_preserves_sizes_and_consumes_guest_once(self):
        device = Client()
        self.signin(device)
        self.add(device, quantity=2)
        self.add(self.client, quantity=1)
        self.add(self.client, size='xl', quantity=2)
        guest_pk = Cart.objects.get(user__isnull=True).pk
        self.signin(self.client)
        saved = Cart.objects.get(user=self.user)
        self.assertEqual(dict(saved.items.values_list('size', 'quantity')), {'s': 3, 'xl': 2})
        self.assertFalse(Cart.objects.filter(pk=guest_pk).exists())
        self.client.post(reverse('accounts:logout'))
        self.signin(self.client)
        self.assertEqual(self.client.get(reverse('cart')).context['quantity'], 5)

    def test_saved_cart_mutations_cannot_access_another_customer(self):
        self.signin(self.client)
        self.add(self.client)
        item = CartItem.objects.get()
        intruder = Client()
        self.signin(intruder, self.other_user)
        self.add(intruder)
        for route in ['remove_cart', 'increase_cart', 'decrease_cart', 'update_cart']:
            self.assertEqual(intruder.post(reverse(route, args=[item.pk]), {'quantity': 2}).status_code, 404)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 1)
        self.assertEqual(Client().post(reverse('remove_cart', args=[item.pk])).status_code, 404)

    def test_overstock_merge_is_visible_and_blocks_shipping_without_losing_items(self):
        self.signin(self.client)
        self.add(self.client, quantity=4)
        guest = Client()
        self.add(guest, quantity=4)
        self.signin(guest)
        response = guest.get(reverse('cart'))
        self.assertEqual(response.context['quantity'], 8)
        self.assertTrue(response.context['has_stock_issues'])
        self.assertContains(response, 'Only 5 item(s) are available')
        self.assertFalse(Order.objects.exists())

    def draft(self, cart, user=None):
        order = Order.objects.create(cart=cart, user=user, total_amount=2000, shipping_name='Asha Rao', shipping_address_line1='12 Market Road', shipping_city='Chennai')
        OrderItem.objects.create(order=order, product=self.product, product_name=self.product.product_name, size='s', quantity=2, unit_price=1000)
        return order

    def test_guest_shipping_draft_is_owned_and_restored_across_devices(self):
        self.add(self.client, quantity=2)
        guest_cart = Cart.objects.get()
        order = self.draft(guest_cart)
        session = self.client.session
        session['checkout_order_id'] = order.pk
        session.save()
        self.signin(self.client)
        order.refresh_from_db()
        self.assertEqual(order.user_id, self.user.pk)
        fresh = Client()
        self.signin(fresh)
        self.assertEqual(fresh.get(reverse('orders:shipping_review')).context['order'], order)
        self.assertContains(fresh.get(reverse('orders:shipping_details')), '12 Market Road')
        other = Client()
        self.signin(other, self.other_user)
        session = other.session
        session['checkout_order_id'] = order.pk
        session.save()
        self.assertRedirects(other.get(reverse('orders:shipping_review')), reverse('orders:shipping_details'), fetch_redirect_response=False)

    def test_guest_draft_survives_merge_and_review_detects_changed_bag(self):
        self.signin(self.client)
        self.add(self.client, quantity=1)
        guest = Client()
        self.add(guest, quantity=2)
        guest_cart = Cart.objects.get(user__isnull=True)
        order = self.draft(guest_cart)
        self.signin(guest)
        order.refresh_from_db()
        self.assertEqual(order.cart_id, Cart.objects.get(user=self.user).pk)
        self.assertEqual(order.user_id, self.user.pk)
        self.assertRedirects(guest.get(reverse('orders:shipping_review')), reverse('orders:shipping_details'), fetch_redirect_response=False)
        self.assertContains(guest.get(reverse('orders:shipping_details')), '12 Market Road')

    def test_password_change_keeps_saved_cart(self):
        self.signin(self.client)
        self.add(self.client, quantity=2)
        self.client.post(reverse('accounts:password_change'), {'old_password': self.password, 'new_password1': 'Golden-forest-87!', 'new_password2': 'Golden-forest-87!'})
        self.assertEqual(self.client.get(reverse('cart')).context['quantity'], 2)
        self.assertEqual(Cart.objects.get(user=self.user).items.get().quantity, 2)
