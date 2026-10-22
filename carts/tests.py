from django.db import IntegrityError, transaction
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse

from category.models import Category, Department
from store.models import Product, ProductInventory

from .models import Cart, CartItem


class CartCounterTests(TestCase):
    def test_browsing_does_not_create_cart_or_session(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.context['cart_count'], 0)
        self.assertContains(response, 'Shopping bag, 0 items')
        self.assertIsNone(response.wsgi_request.session.session_key)
        self.assertNotIn('sessionid', response.cookies)
        self.assertFalse(Cart.objects.exists())

    def test_counter_counts_active_units_and_isolates_sessions(self):
        department = Department.objects.create(department_name='Women', slug='women')
        category = Category.objects.create(category_name='Clothing', slug='clothing', department=department)
        product = Product.objects.create(product_name='Dress', slug='dress', category=category, price=1000, color='Red', size_type='clothing')
        ProductInventory.objects.create(product=product, size='s', quantity=5)
        ProductInventory.objects.create(product=product, size='xl', quantity=5)
        self.client.post(reverse('add_cart', args=[product.pk]), {'size': 's', 'quantity': 2})
        self.client.post(reverse('add_cart', args=[product.pk]), {'size': 'xl', 'quantity': 3})
        other_client = Client()
        other_client.post(reverse('add_cart', args=[product.pk]), {'size': 's'})
        response = self.client.get(reverse('home'))
        self.assertEqual(response.context['cart_count'], 5)
        self.assertContains(response, 'Shopping bag, 5 items')
        CartItem.objects.filter(cart__cart_id=self.client.session.session_key, size='xl').update(is_active=False)
        self.assertEqual(self.client.get(reverse('home')).context['cart_count'], 2)
        self.assertEqual(other_client.get(reverse('home')).context['cart_count'], 1)
        self.client.post(reverse('remove_cart', args=[CartItem.objects.get(cart__cart_id=self.client.session.session_key, size='s').pk]))
        self.assertEqual(self.client.get(reverse('home')).context['cart_count'], 0)


class CartViewTests(TestCase):
    def test_empty_cart_renders_the_cart_template(self):
        response = self.client.get(reverse('cart'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'carts/cart.html')
        self.assertEqual(response.context['total'], 0)
        self.assertEqual(response.context['quantity'], 0)


class CartMutationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        department = Department.objects.create(department_name='Women', slug='women')
        category = Category.objects.create(category_name='Clothing', slug='clothing', department=department)
        cls.product = Product.objects.create(
            product_name='Dress', slug='dress', color='Red', price=1000,
            category=category, size_type=Product.SizeType.CLOTHING,
        )
        cls.small_stock = ProductInventory.objects.create(product=cls.product, size='s', quantity=3)
        ProductInventory.objects.create(product=cls.product, size='xl', quantity=2)
        ProductInventory.objects.create(product=cls.product, size='xxl', quantity=0)
        cls.saree = Product.objects.create(
            product_name='Saree', slug='saree', color='Gold', price=2000,
            category=category, size_type=Product.SizeType.FREE_SIZE,
        )
        ProductInventory.objects.create(product=cls.saree, size='free_size', quantity=4)
        cls.jewellery = Product.objects.create(
            product_name='Necklace', slug='necklace', color='Gold', price=500,
            category=category, size_type=Product.SizeType.NO_SIZE,
        )
        ProductInventory.objects.create(product=cls.jewellery, size='no_size', quantity=5)

    def add_item(self, product=None, **data):
        return self.client.post(reverse('add_cart', args=[(product or self.product).pk]), data)

    def test_same_size_increments_and_different_sizes_remain_separate(self):
        self.add_item(size='s')
        self.add_item(size='s')
        self.add_item(size='xl')

        self.assertEqual(list(CartItem.objects.order_by('size').values_list('size', 'quantity')), [('s', 2), ('xl', 1)])
        response = self.client.get(reverse('cart'))
        self.assertEqual(response.context['quantity'], 3)
        self.assertEqual(response.context['total'], 3000)
        self.assertContains(response, 'Size: S')
        self.assertContains(response, 'Size: XL')

    def test_clothing_requires_a_valid_size(self):
        for size in ['', 'm', 'free_size', 'no_size']:
            with self.subTest(size=size):
                response = self.client.post(reverse('add_cart', args=[self.product.pk]), {'size': size}, follow=True)
                self.assertContains(response, 'role="alert"')
                self.assertFalse(CartItem.objects.exists())

    def test_unsized_and_free_size_products_choose_their_inventory_automatically(self):
        self.add_item(self.saree)
        self.add_item(self.jewellery, quantity=2)
        self.assertEqual(CartItem.objects.get(product=self.saree).size, 'free_size')
        item = CartItem.objects.get(product=self.jewellery)
        self.assertEqual((item.size, item.quantity), ('no_size', 2))

    def test_incompatible_size_for_unsized_products_is_rejected(self):
        self.add_item(self.jewellery, size='s')
        self.add_item(self.saree, size='xl')
        self.assertFalse(CartItem.objects.exists())

    def test_invalid_add_quantities_are_rejected(self):
        for quantity in ['0', '-1', '1.5', 'abc', '2147483648']:
            with self.subTest(quantity=quantity):
                self.add_item(size='s', quantity=quantity)
                self.assertFalse(CartItem.objects.exists())

    def test_addition_checks_combined_quantity_against_size_stock(self):
        self.add_item(size='s', quantity=2)
        response = self.client.post(reverse('add_cart', args=[self.product.pk]), {'size': 's', 'quantity': 2}, follow=True)
        self.assertContains(response, 'Only 3 item(s) are available')
        self.assertEqual(CartItem.objects.get().quantity, 2)
        self.small_stock.refresh_from_db()
        self.assertEqual(self.small_stock.quantity, 3)

    def test_zero_or_missing_inventory_is_rejected(self):
        self.add_item(size='xxl')
        ProductInventory.objects.filter(product=self.product, size='xl').delete()
        self.add_item(size='xl')
        self.assertFalse(CartItem.objects.exists())

    def test_missing_or_unavailable_products_return_404(self):
        self.assertEqual(self.client.post(reverse('add_cart', args=[999999]), {'size': 's'}).status_code, 404)
        Product.objects.filter(pk=self.product.pk).update(is_available=False)
        self.assertEqual(self.add_item(size='s').status_code, 404)

    def test_update_increase_and_decrease_change_quantity_and_totals(self):
        self.add_item(size='s')
        item = CartItem.objects.get()
        self.client.post(reverse('update_cart', args=[item.pk]), {'quantity': 2})
        self.client.post(reverse('increase_cart', args=[item.pk]))
        response = self.client.post(reverse('decrease_cart', args=[item.pk]), follow=True)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 2)
        self.assertEqual(response.context['quantity'], 2)
        self.assertEqual(response.context['total'], 2000)

    def test_update_and_increase_cannot_exceed_stock(self):
        self.add_item(size='s', quantity=3)
        item = CartItem.objects.get()
        self.client.post(reverse('increase_cart', args=[item.pk]))
        self.client.post(reverse('update_cart', args=[item.pk]), {'quantity': 4})
        item.refresh_from_db()
        self.assertEqual(item.quantity, 3)

    def test_invalid_update_quantities_leave_item_unchanged(self):
        self.add_item(size='s')
        item = CartItem.objects.get()
        for quantity in ['', '0', '-1', 'abc', '1.5', '2147483648']:
            with self.subTest(quantity=quantity):
                self.client.post(reverse('update_cart', args=[item.pk]), {'quantity': quantity})
                item.refresh_from_db()
                self.assertEqual(item.quantity, 1)

    def test_decreasing_last_unit_removes_item(self):
        self.add_item(size='s')
        response = self.client.post(reverse('decrease_cart', args=[CartItem.objects.get().pk]), follow=True)
        self.assertFalse(CartItem.objects.exists())
        self.assertEqual(response.context['total'], 0)

    def test_removal_only_removes_selected_size(self):
        self.add_item(size='s')
        self.add_item(size='xl')
        self.client.post(reverse('remove_cart', args=[CartItem.objects.get(size='s').pk]))
        self.assertEqual(CartItem.objects.get().size, 'xl')

    def test_all_mutations_require_post(self):
        self.add_item(size='s')
        item = CartItem.objects.get()
        routes = [reverse('add_cart', args=[self.product.pk])] + [
            reverse(name, args=[item.pk])
            for name in ['update_cart', 'increase_cart', 'decrease_cart', 'remove_cart']
        ]
        for route in routes:
            for method in ['get', 'head', 'put', 'delete']:
                with self.subTest(route=route, method=method):
                    self.assertEqual(getattr(self.client, method)(route).status_code, 405)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 1)

    def test_all_mutations_require_csrf(self):
        self.add_item(size='s')
        item = CartItem.objects.get()
        client = Client(enforce_csrf_checks=True)
        client.cookies = self.client.cookies.copy()
        routes = [reverse('add_cart', args=[self.product.pk])] + [
            reverse(name, args=[item.pk])
            for name in ['update_cart', 'increase_cart', 'decrease_cart', 'remove_cart']
        ]
        for route in routes:
            with self.subTest(route=route):
                self.assertEqual(client.post(route, {'size': 's', 'quantity': 2}).status_code, 403)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 1)

    def test_other_sessions_cannot_view_or_modify_items(self):
        self.add_item(size='s')
        item = CartItem.objects.get()
        other_client = Client()
        self.assertEqual(other_client.get(reverse('cart')).context['quantity'], 0)
        for name in ['update_cart', 'increase_cart', 'decrease_cart', 'remove_cart']:
            with self.subTest(route=name):
                self.assertEqual(other_client.post(reverse(name, args=[item.pk]), {'quantity': 2}).status_code, 404)
        other_client.post(reverse('add_cart', args=[self.product.pk]), {'size': 's'})
        self.assertEqual(Cart.objects.count(), 2)
        self.assertEqual(other_client.post(reverse('remove_cart', args=[item.pk])).status_code, 404)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 1)

    def test_stock_reduction_is_displayed_and_quantity_can_be_corrected(self):
        self.add_item(size='s', quantity=3)
        item = CartItem.objects.get()
        ProductInventory.objects.filter(pk=self.small_stock.pk).update(quantity=1)
        response = self.client.get(reverse('cart'))
        self.assertContains(response, 'Only 1 item(s) are available')
        self.assertNotContains(response, f'href="{reverse("orders:shipping_details")}"')
        self.assertContains(response, 'Update or remove the marked items to continue.')
        self.client.post(reverse('increase_cart', args=[item.pk]))
        item.refresh_from_db()
        self.assertEqual(item.quantity, 3)
        self.client.post(reverse('update_cart', args=[item.pk]), {'quantity': 1})
        item.refresh_from_db()
        self.assertEqual(item.quantity, 1)

        response = self.client.get(reverse('cart'))
        self.assertContains(response, f'action="{reverse("buy_bag")}"')

    def test_unavailable_product_can_be_removed_but_cannot_be_increased(self):
        self.add_item(size='s')
        item = CartItem.objects.get()
        Product.objects.filter(pk=self.product.pk).update(is_available=False)
        response = self.client.post(reverse('increase_cart', args=[item.pk]), follow=True)
        self.assertContains(response, 'This product is no longer available.')
        item.refresh_from_db()
        self.assertEqual(item.quantity, 1)
        self.client.post(reverse('remove_cart', args=[item.pk]))
        self.assertFalse(CartItem.objects.exists())

    def test_inactive_item_is_reactivated_without_reusing_its_old_quantity(self):
        self.add_item(size='s')
        item = CartItem.objects.get()
        item.quantity = 3
        item.is_active = False
        item.save()
        self.add_item(size='s')
        item.refresh_from_db()
        self.assertTrue(item.is_active)
        self.assertEqual(item.quantity, 1)

    def test_legacy_clothing_item_needs_size_selection_and_remains_removable(self):
        self.add_item(size='s')
        item = CartItem.objects.get()
        item.size = ''
        item.save()
        response = self.client.get(reverse('cart'))
        self.assertContains(response, 'add it again with a valid size')
        self.client.post(reverse('increase_cart', args=[item.pk]))
        item.refresh_from_db()
        self.assertEqual(item.quantity, 1)
        self.client.post(reverse('remove_cart', args=[item.pk]))
        self.assertFalse(CartItem.objects.exists())

    def test_database_prevents_duplicate_product_size_rows(self):
        self.add_item(size='s')
        item = CartItem.objects.get()
        with self.assertRaises(IntegrityError), transaction.atomic():
            CartItem.objects.create(cart=item.cart, product=self.product, size='s')

    def test_catalog_sends_sized_products_to_detail_page(self):
        response = self.client.get(reverse('store:store'))
        self.assertContains(response, f'href="{self.product.get_url()}"')
        self.assertContains(response, 'Choose size')
        self.assertNotContains(response, f'id="size-{self.product.pk}"')
        self.assertNotContains(response, f'action="{reverse("add_cart", args=[self.product.pk])}"')

    def test_catalog_does_not_offer_addition_for_missing_or_incompatible_stock(self):
        ProductInventory.objects.filter(product=self.product).update(quantity=0)
        ProductInventory.objects.create(product=self.product, size='free_size', quantity=5)
        ProductInventory.objects.filter(product=self.saree).delete()
        for route in ['store:store', 'store:search']:
            with self.subTest(route=route):
                response = self.client.get(reverse(route), {'keyword': 'Dress'})
                self.assertNotContains(response, f'action="{reverse("add_cart", args=[self.product.pk])}"')
                self.assertNotContains(response, f'action="{reverse("add_cart", args=[self.saree.pk])}"')
                self.assertContains(response, 'Out of stock')


class CartSizeMigrationTests(TransactionTestCase):
    def test_migration_preserves_legacy_items_and_assigns_only_known_sizes(self):
        from django.db import connection
        from django.db.migrations.executor import MigrationExecutor

        executor = MigrationExecutor(connection)
        latest_targets = executor.loader.graph.leaf_nodes()
        self.addCleanup(lambda: MigrationExecutor(connection).migrate(latest_targets))
        executor.migrate([('carts', '0001_initial')])
        old_apps = executor.loader.project_state([
            ('carts', '0001_initial'),
            ('store', '0008_alter_product_size_type'),
        ]).apps
        old_category = old_apps.get_model('category', 'Category').objects.create(
            category_name='Legacy', slug='legacy',
        )
        old_cart = old_apps.get_model('carts', 'Cart').objects.create(cart_id='legacy-session')
        for size_type in ['free_size', 'no_size', 'clothing']:
            product = old_apps.get_model('store', 'Product').objects.create(
                product_name=size_type, slug=size_type, color='Red', price=1000,
                category=old_category, size_type=size_type,
            )
            old_apps.get_model('carts', 'CartItem').objects.create(
                cart=old_cart, product=product, quantity=2,
            )
        executor = MigrationExecutor(connection)
        executor.migrate(latest_targets)
        self.assertEqual(dict(CartItem.objects.values_list('product__size_type', 'size')), {
            'free_size': 'free_size', 'no_size': 'no_size', 'clothing': '',
        })
        self.assertEqual(list(CartItem.objects.values_list('quantity', flat=True)), [2, 2, 2])
