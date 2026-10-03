from django.test import TestCase
from django.urls import reverse


class CartViewTests(TestCase):
    def test_empty_cart_renders_the_cart_template(self):
        response = self.client.get(reverse('cart'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'carts/cart.html')
        self.assertEqual(response.context['total'], 0)
        self.assertEqual(response.context['quantity'], 0)
