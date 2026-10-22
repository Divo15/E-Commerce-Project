from django.contrib import admin
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import Account
from carts.models import CartItem
from category.models import Category, Department
from store.models import Product, ProductInventory

from .forms import ShippingDetailsForm
from .models import Order


class ShippingDetailsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        department = Department.objects.create(department_name='Women', slug='women')
        category = Category.objects.create(category_name='Clothing', slug='clothing', department=department)
        cls.product = Product.objects.create(
            product_name='Dress', slug='dress', color='Red', price=1500,
            category=category, size_type=Product.SizeType.CLOTHING,
        )
        cls.inventory = ProductInventory.objects.create(product=cls.product, size='s', quantity=5)
        ProductInventory.objects.create(product=cls.product, size='xl', quantity=3)
        cls.user = Account.objects.create_user(
            first_name='Asha', last_name='Rao', username='asha',
            email='asha@example.com', password='A-long-test-password-42',
        )
        cls.user.is_active = True
        cls.user.phone_number = '9876543210'
        cls.user.save()

    def setUp(self):
        self.shipping_url = reverse('orders:shipping_details')
        self.review_url = reverse('orders:shipping_review')
        self.data = {
            'shipping_name': 'Asha Rao',
            'shipping_email': 'asha@example.com',
            'shipping_phone': '+91 98765 43210',
            'shipping_address_line1': '12 Market Road',
            'shipping_address_line2': 'Central area',
            'shipping_city': 'Chennai',
            'shipping_state': 'Tamil Nadu',
            'shipping_postal_code': '600001',
            'shipping_country': 'India',
            'shipping_landmark': 'Near the library',
            'shipping_instructions': 'Ring the bell on arrival.',
        }

    def add_item(self, client=None, size='s', quantity=2):
        (client or self.client).post(reverse('add_cart', args=[self.product.pk]), {
            'size': size, 'quantity': quantity,
        })

    def test_empty_cart_redirects_to_bag_without_creating_order(self):
        for method in ['get', 'post']:
            with self.subTest(method=method):
                response = getattr(self.client, method)(self.shipping_url, self.data if method == 'post' else {})
                self.assertRedirects(response, reverse('cart'))
                self.assertFalse(Order.objects.exists())

    def test_cart_links_to_shipping_and_get_does_not_create_an_order(self):
        self.add_item()
        self.assertContains(self.client.get(reverse('cart')), reverse('buy_bag'))
        response = self.client.get(self.shipping_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'orders/shipping_details.html')
        self.assertEqual(response.context['total'], 3000)
        self.assertEqual(response.context['form']['shipping_country'].value(), 'India')
        self.assertContains(response, 'autocomplete="shipping address-line1"')
        self.assertFalse(Order.objects.exists())
        self.assertIn('no-store', response['Cache-Control'])

    def test_guest_submission_saves_address_and_size_specific_order_snapshot(self):
        self.add_item()
        self.add_item(size='xl', quantity=1)
        data = {**self.data, 'total_amount': '1', 'status': 'paid', 'user': str(self.user.pk)}
        response = self.client.post(self.shipping_url, data)
        self.assertRedirects(response, self.review_url)
        order = Order.objects.get()
        self.assertEqual(order.shipping_name, 'Asha Rao')
        self.assertEqual(order.shipping_address_line1, '12 Market Road')
        self.assertEqual(order.shipping_instructions, self.data['shipping_instructions'])
        self.assertEqual(order.total_amount, 4500)
        self.assertEqual(order.status, Order.PaymentStatus.PENDING)
        self.assertIsNone(order.user)
        self.assertIsNone(order.paid_at)
        self.assertEqual(list(order.items.order_by('size').values_list('size', 'quantity', 'unit_price')), [
            ('s', 2, 1500), ('xl', 1, 1500),
        ])
        self.assertEqual(CartItem.objects.count(), 2)
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.quantity, 5)

    def test_authenticated_contact_details_are_prefilled_and_user_is_saved(self):
        self.client.force_login(self.user)
        self.add_item()
        form = self.client.get(self.shipping_url).context['form']
        self.assertEqual(form['shipping_name'].value(), 'Asha Rao')
        self.assertEqual(form['shipping_email'].value(), self.user.email)
        self.assertEqual(form['shipping_phone'].value(), self.user.phone_number)
        self.client.post(self.shipping_url, self.data)
        self.assertEqual(Order.objects.get().user, self.user)

    def test_missing_required_fields_retain_input_without_creating_order(self):
        self.add_item()
        for field in ShippingDetailsForm().fields:
            if field in {'shipping_address_line2', 'shipping_landmark', 'shipping_instructions'}:
                continue
            with self.subTest(field=field):
                response = self.client.post(self.shipping_url, {**self.data, field: '   '})
                self.assertEqual(response.status_code, 200)
                self.assertIn(field, response.context['form'].errors)
                self.assertContains(response, 'Check your details')
                self.assertFalse(Order.objects.exists())

    def test_invalid_contact_and_pin_are_rejected(self):
        self.add_item()
        for field, value in [
            ('shipping_email', 'not-an-email'), ('shipping_phone', '123'),
            ('shipping_phone', '1234567abc'), ('shipping_phone', '1234567890123456'),
            ('shipping_postal_code', '12345'), ('shipping_postal_code', '000001'),
            ('shipping_postal_code', 'ABCDEF'),
        ]:
            with self.subTest(field=field, value=value):
                response = self.client.post(self.shipping_url, {**self.data, field: value})
                self.assertIn(field, response.context['form'].errors)
                self.assertFalse(Order.objects.exists())

    def test_international_address_and_optional_fields_are_supported(self):
        self.add_item()
        data = {**self.data, 'shipping_country': 'United Kingdom', 'shipping_postal_code': 'SW1A 1AA'}
        for field in ['shipping_address_line2', 'shipping_landmark', 'shipping_instructions']:
            del data[field]
        self.assertRedirects(self.client.post(self.shipping_url, data), self.review_url)
        order = Order.objects.get()
        self.assertEqual(order.shipping_postal_code, 'SW1A 1AA')
        self.assertEqual(order.shipping_address_line2, '')

    def test_input_is_trimmed_and_india_country_alias_is_normalized(self):
        self.add_item()
        self.client.post(self.shipping_url, {**self.data, 'shipping_name': ' Asha Rao ', 'shipping_country': ' in '})
        order = Order.objects.get()
        self.assertEqual(order.shipping_name, 'Asha Rao')
        self.assertEqual(order.shipping_country, 'India')

    def test_overlong_address_is_rejected(self):
        self.add_item()
        response = self.client.post(self.shipping_url, {**self.data, 'shipping_address_line1': 'x' * 201})
        self.assertIn('shipping_address_line1', response.context['form'].errors)
        self.assertFalse(Order.objects.exists())

    def test_repeated_submission_updates_same_draft_and_refreshes_items(self):
        self.add_item()
        self.client.post(self.shipping_url, self.data)
        order = Order.objects.get()
        self.client.post(reverse('update_cart', args=[CartItem.objects.get().pk]), {'quantity': 3})
        self.client.post(self.shipping_url, {**self.data, 'shipping_address_line1': '24 Market Road'})
        self.assertEqual(Order.objects.count(), 1)
        order.refresh_from_db()
        self.assertEqual(order.shipping_address_line1, '24 Market Road')
        self.assertEqual(order.total_amount, 4500)
        self.assertEqual(order.items.get().quantity, 3)
        response = self.client.get(self.shipping_url)
        self.assertEqual(response.context['form']['shipping_address_line1'].value(), '24 Market Road')

    def test_invalid_edit_preserves_previously_saved_address(self):
        self.add_item()
        self.client.post(self.shipping_url, self.data)
        self.client.post(self.shipping_url, {**self.data, 'shipping_name': ''})
        self.assertEqual(Order.objects.get().shipping_name, 'Asha Rao')

    def test_stock_is_rechecked_before_saving(self):
        self.add_item()
        ProductInventory.objects.filter(pk=self.inventory.pk).update(quantity=1)
        response = self.client.post(self.shipping_url, self.data)
        self.assertContains(response, 'Only 1 item(s) are available')
        self.assertFalse(Order.objects.exists())

    def test_unavailable_product_or_legacy_size_blocks_submission(self):
        self.add_item()
        item = CartItem.objects.get()
        item.size = ''
        item.save()
        self.assertContains(self.client.post(self.shipping_url, self.data), 'valid size')
        self.assertFalse(Order.objects.exists())
        item.size = 's'
        item.save()
        Product.objects.filter(pk=self.product.pk).update(is_available=False)
        self.assertContains(self.client.post(self.shipping_url, self.data), 'no longer available')
        self.assertFalse(Order.objects.exists())

    def test_other_sessions_cannot_access_or_overwrite_shipping_details(self):
        self.add_item()
        self.client.post(self.shipping_url, self.data)
        order = Order.objects.get()
        other_client = Client()
        self.add_item(client=other_client)
        session = other_client.session
        session['checkout_order_id'] = order.pk
        session.save()
        self.assertRedirects(other_client.get(self.review_url), self.shipping_url)
        form = other_client.get(self.shipping_url).context['form']
        self.assertNotEqual(form['shipping_address_line1'].value(), order.shipping_address_line1)
        other_client.post(self.shipping_url, {**self.data, 'shipping_address_line1': 'Different address'})
        order.refresh_from_db()
        self.assertEqual(order.shipping_address_line1, '12 Market Road')
        self.assertEqual(Order.objects.count(), 2)

    def test_paid_or_payment_started_order_is_never_overwritten(self):
        self.add_item()
        self.client.post(self.shipping_url, self.data)
        order = Order.objects.get()
        order.status = Order.PaymentStatus.PAID
        order.save()
        self.client.post(self.shipping_url, {**self.data, 'shipping_address_line1': 'New address'})
        order.refresh_from_db()
        self.assertEqual(order.shipping_address_line1, '12 Market Road')
        draft = Order.objects.exclude(pk=order.pk).get()
        draft.stripe_checkout_session_id = 'cs_test_pending'
        draft.save()
        self.client.post(self.shipping_url, {**self.data, 'shipping_address_line1': 'Another address'})
        draft.refresh_from_db()
        self.assertEqual(draft.shipping_address_line1, 'New address')
        self.assertEqual(Order.objects.count(), 3)

    def test_review_displays_saved_address_and_does_not_claim_order_is_placed(self):
        self.add_item()
        self.client.post(self.shipping_url, self.data)
        Product.objects.filter(pk=self.product.pk).update(product_name='Changed name')
        response = self.client.get(self.review_url)
        self.assertContains(response, '12 Market Road')
        self.assertContains(response, 'Dress')
        self.assertNotContains(response, 'Changed name')
        self.assertContains(response, 'Your order has not been placed')
        self.assertIn('no-store', response['Cache-Control'])

    def test_review_requires_resave_after_cart_quantity_changes(self):
        self.add_item()
        self.client.post(self.shipping_url, self.data)
        order = Order.objects.get()
        self.client.post(reverse('update_cart', args=[CartItem.objects.get().pk]), {'quantity': 3})

        response = self.client.get(self.review_url, follow=True)
        self.assertRedirects(response, self.shipping_url)
        self.assertContains(response, 'Your bag changed. Save shipping details again')
        self.assertEqual(response.context['form']['shipping_address_line1'].value(), '12 Market Road')
        self.assertEqual(order.total_amount, 3000)

        self.client.post(self.shipping_url, self.data)
        order.refresh_from_db()
        self.assertEqual(order.total_amount, 4500)
        self.assertEqual(order.items.get().quantity, 3)
        self.assertEqual(self.client.get(self.review_url).status_code, 200)

    def test_review_requires_resave_after_product_price_changes(self):
        self.add_item()
        self.client.post(self.shipping_url, self.data)
        Product.objects.filter(pk=self.product.pk).update(price=2000)

        self.assertRedirects(self.client.get(self.review_url), self.shipping_url)
        self.client.post(self.shipping_url, self.data)
        self.assertEqual(Order.objects.get().total_amount, 4000)
        self.assertEqual(self.client.get(self.review_url).status_code, 200)

    def test_saved_content_is_escaped(self):
        self.add_item()
        response = self.client.post(self.shipping_url, {
            **self.data, 'shipping_instructions': '<script>alert(1)</script>',
        }, follow=True)
        self.assertContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;')
        self.assertNotContains(response, '<script>alert(1)</script>')

    def test_shipping_submission_requires_csrf(self):
        self.add_item()
        client = Client(enforce_csrf_checks=True)
        client.cookies = self.client.cookies.copy()
        self.assertEqual(client.post(self.shipping_url, self.data).status_code, 403)
        self.assertFalse(Order.objects.exists())

    def test_unsupported_methods_are_rejected(self):
        self.add_item()
        self.assertEqual(self.client.delete(self.shipping_url).status_code, 405)
        self.assertEqual(self.client.post(self.review_url).status_code, 405)

    def test_owner_can_read_shipping_details_in_admin(self):
        self.add_item()
        self.client.post(self.shipping_url, self.data)
        self.user.is_admin = True
        self.user.is_staff = True
        self.user.is_superadmin = True
        self.user.save()
        self.client.force_login(self.user)
        self.assertIn(Order, admin.site._registry)
        response = self.client.get(reverse('admin:orders_order_change', args=[Order.objects.get().pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '12 Market Road')
        self.assertContains(response, 'Pending')
