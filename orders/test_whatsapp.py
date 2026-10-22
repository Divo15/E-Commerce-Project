from urllib.parse import parse_qs, urlsplit

from django.test import Client, TestCase, override_settings
from django.urls import reverse

from accounts.models import Account
from carts.models import CartItem
from category.models import Category, Department
from store.models import Product, ProductInventory
from .models import Order


@override_settings(WHATSAPP_ORDER_NUMBER='6583952511', PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class WhatsAppOrderingTests(TestCase):
    def setUp(self):
        self.user = Account.objects.create_user('Meera', 'Rao', 'meera', 'meera@example.com', 'Velvet-forest-43!')
        self.user.is_active = True
        self.user.phone_number = '+91 9876543210'
        self.user.city = 'Chennai'
        self.user.postal_code = '600001'
        self.user.save()
        department = Department.objects.create(department_name='Women', slug='women')
        category = Category.objects.create(category_name='Dresses', slug='dresses', department=department)
        self.product = Product.objects.create(product_name='Floral dress & dupatta', slug='floral-dress', category=category, color='Red', price=1500, size_type='clothing')
        ProductInventory.objects.create(product=self.product, size='s', quantity=5)
        self.url = reverse('store:buy_now', args=[self.product.pk])

    def test_buy_now_prefills_saved_details_and_selected_item_without_placing_order(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {'size': 's', 'quantity': 2, 'price': 1, 'email': 'spoof@example.com', 'phone': '123'})
        self.assertEqual(response.status_code, 302)
        link = urlsplit(response.url)
        self.assertEqual((link.scheme, link.netloc, link.path), ('https', 'wa.me', '/6583952511'))
        text = parse_qs(link.query)['text'][0]
        for expected in ['Meera Rao', self.user.email, self.user.phone_number, 'Chennai', '600001', self.product.product_name, 'Size: S', 'Quantity: 2', '₹1,500', '₹3,000', self.product.get_url()]:
            self.assertIn(expected, text)
        self.assertNotIn('spoof@example.com', text)
        self.assertNotIn('Photo:', text)
        self.assertFalse(Order.objects.exists())
        self.assertFalse(CartItem.objects.exists())
        self.assertEqual(ProductInventory.objects.get().quantity, 5)

    def test_guest_must_sign_in_and_selection_is_kept(self):
        response = self.client.post(self.url, {'size': 's', 'quantity': 2})
        self.assertEqual(response.status_code, 302)
        next_url = parse_qs(urlsplit(response.url).query)['next'][0]
        self.assertEqual(urlsplit(response.url).path, reverse('accounts:login'))
        self.assertEqual(parse_qs(urlsplit(next_url).query), {'size': ['s'], 'quantity': ['2']})
        self.assertNotIn('wa.me', response.url)

    def test_missing_contact_details_are_completed_and_retained(self):
        self.user.city = ''
        self.user.postal_code = ''
        self.user.save()
        self.client.force_login(self.user)
        response = self.client.post(self.url, {'size': 's'})
        self.assertEqual(urlsplit(response.url).path, reverse('accounts:details'))
        response = self.client.post(reverse('accounts:details'), {'first_name': 'Meera', 'last_name': 'Rao', 'phone_number': '+91 9876543210', 'city': 'Chennai', 'postal_code': '600001', 'next': self.product.get_url()})
        self.assertRedirects(response, self.product.get_url())
        self.user.refresh_from_db()
        self.assertEqual(self.user.city, 'Chennai')
        self.assertIn('wa.me', self.client.post(self.url, {'size': 's'}).url)

    def test_invalid_or_out_of_stock_selection_cannot_open_whatsapp(self):
        self.client.force_login(self.user)
        for data in [{'size': 's', 'quantity': 6}, {'size': 'xl'}, {'size': 'wrong'}, {'size': 's', 'quantity': 0}]:
            response = self.client.post(self.url, data)
            self.assertRedirects(response, self.product.get_url())
        self.assertEqual(self.client.get(self.url).status_code, 405)
        self.assertEqual(Client(enforce_csrf_checks=True).post(self.url, {'size': 's'}).status_code, 403)

    def test_bag_handoff_contains_only_current_customers_items_and_keeps_bag(self):
        self.client.force_login(self.user)
        self.client.post(reverse('add_cart', args=[self.product.pk]), {'size': 's', 'quantity': 2})
        response = self.client.post(reverse('buy_bag'))
        self.assertEqual(urlsplit(response.url).path, '/6583952511')
        text = parse_qs(urlsplit(response.url).query)['text'][0]
        self.assertIn('Item total: ₹3,000', text)
        self.assertEqual(CartItem.objects.get().quantity, 2)
        self.assertFalse(Order.objects.exists())
        other = Account.objects.create_user('Asha', 'Rao', 'asha', 'asha@example.com', 'password')
        other.is_active = True
        other.phone_number, other.city, other.postal_code = '+91 9876543210', 'Chennai', '600001'
        other.save()
        other_client = Client()
        other_client.force_login(other)
        self.assertRedirects(other_client.post(reverse('buy_bag')), reverse('cart'))

    def test_contact_editor_rejects_external_return_url(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('accounts:details'), {'first_name': 'Meera', 'last_name': 'Rao', 'phone_number': '9876543210', 'city': 'Chennai', 'postal_code': '600001', 'next': 'https://example.com'})
        self.assertRedirects(response, reverse('accounts:account'))

    @override_settings(ACCOUNT_PUBLIC_ORIGIN='https://shop.example')
    def test_three_product_bag_preserves_every_item_and_contact_details_in_encoded_message(self):
        self.product.price = 1000
        self.product.image_1 = 'photos/products/floral-dress.jpg'
        self.product.save(update_fields=['price', 'image_1'])
        products = [self.product]
        for name, slug, price in [
            ('Brown Printed V-Neck Kurta Set with Matching Dupatta', 'brown-kurta', 968),
            ('Pastel Embroidered Saree with Peacock & Floral Border', 'pastel-saree', 1000),
        ]:
            product = Product.objects.create(product_name=name, slug=slug, category=self.product.category, color='Pastel', price=price, size_type='free_size', image_1=f'photos/products/{slug}.jpg')
            ProductInventory.objects.create(product=product, size='free_size', quantity=5)
            products.append(product)
        self.client.force_login(self.user)
        for index, product in enumerate(products):
            self.client.post(reverse('add_cart', args=[product.pk]), {'size': 's' if index == 0 else 'free_size', 'quantity': 1})

        response = self.client.post(reverse('buy_bag'))
        self.assertEqual(response.status_code, 302)
        link = urlsplit(response.url)
        self.assertEqual(link.netloc, 'wa.me')
        text = parse_qs(link.query)['text'][0]
        for product in products:
            self.assertEqual(text.count(product.product_name), 1)
            self.assertIn(product.get_url(), text)
            self.assertIn(f'Photo: https://shop.example{product.image_1.url}', text)
        self.assertEqual(text.count('Quantity: 1'), 3)
        self.assertEqual(text.count('Photo: '), 3)
        self.assertIn('Item total: ₹2,968', text)
        for value in ['Meera Rao', self.user.email, self.user.phone_number, self.user.city, self.user.postal_code]:
            self.assertIn(value, text)
        self.assertEqual(CartItem.objects.count(), 3)
        self.assertFalse(Order.objects.exists())

    @override_settings(ACCOUNT_PUBLIC_ORIGIN='https://shop.example')
    def test_product_photo_link_uses_saved_image_and_survives_message_encoding(self):
        self.product.image_1 = 'photos/products/floral dress & dupatta.jpg'
        self.product.save(update_fields=['image_1'])
        self.client.force_login(self.user)
        response = self.client.post(self.url, {'size': 's', 'quantity': 1, 'image_url': 'https://spoof.example/other.jpg'})
        text = parse_qs(urlsplit(response.url).query)['text'][0]
        self.assertIn('Photo: https://shop.example/media/photos/products/floral%20dress%20%26%20dupatta.jpg', text)
        self.assertNotIn('spoof.example', text)

    @override_settings(ACCOUNT_PUBLIC_ORIGIN='https://shop.example', MEDIA_URL='https://cdn.example/products/')
    def test_photo_link_preserves_external_media_storage_url(self):
        self.product.image_1 = 'saree.jpg'
        self.product.save(update_fields=['image_1'])
        self.client.force_login(self.user)
        response = self.client.post(self.url, {'size': 's', 'quantity': 1})
        text = parse_qs(urlsplit(response.url).query)['text'][0]
        self.assertIn('Photo: https://cdn.example/products/saree.jpg', text)

    def test_product_and_bag_expose_whatsapp_action(self):
        self.assertContains(self.client.get(self.product.get_url()), f'formaction="{self.url}"')
        self.client.force_login(self.user)
        self.client.post(reverse('add_cart', args=[self.product.pk]), {'size': 's'})
        response = self.client.get(reverse('cart'))
        self.assertContains(response, 'Proceed to WhatsApp to buy')
        self.assertNotContains(response, 'Continue to shipping details')
