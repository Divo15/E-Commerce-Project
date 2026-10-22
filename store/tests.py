from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse

from category.models import Category, Department, SubCategory

from .models import Product, ProductInventory


class ProductDetailTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        department = Department.objects.create(department_name='Women', slug='women')
        category = Category.objects.create(category_name='Clothing', slug='clothing', department=department)
        cls.product = Product.objects.create(
            product_name='Festive dress', slug='festive-dress', category=category,
            color='Red', price=1500, description='Handwoven <script>alert(1)</script>', size_type='clothing',
            image_1='photos/products/front.jpg', image_2='photos/products/back.jpg', image_3='photos/products/detail.jpg',
        )
        ProductInventory.objects.create(product=cls.product, size='s', quantity=3)
        ProductInventory.objects.create(product=cls.product, size='xl', quantity=0)
        ProductInventory.objects.create(product=cls.product, size='free_size', quantity=5)

    def test_detail_renders_gallery_and_only_stocked_valid_sizes(self):
        response = self.client.get(self.product.get_url())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'store/product_detail.html')
        self.assertTemplateUsed(response, 'base.html')
        for image in [self.product.image_1, self.product.image_2, self.product.image_3]:
            self.assertContains(response, image.url)
        self.assertContains(response, 'data-product-gallery')
        self.assertContains(response, 'data-gallery-next')
        self.assertContains(response, 'value="s"')
        self.assertNotContains(response, 'value="xl"')
        self.assertNotContains(response, 'value="free_size"')
        self.assertContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;')
        self.assertNotContains(response, '<script>alert(1)</script>')

    @override_settings(ACCOUNT_PUBLIC_ORIGIN='https://shop.example')
    def test_product_sharing_uses_its_own_photo_and_canonical_url(self):
        response = self.client.get(self.product.get_url() + '?size=s&quantity=2')
        self.assertContains(response, '<meta property="og:image" content="https://shop.example/media/photos/products/front.jpg">')
        self.assertContains(response, f'<meta property="og:url" content="https://shop.example{self.product.get_url()}">')
        self.assertContains(response, '<meta property="og:title" content="Festive dress">')
        self.assertContains(response, '<meta property="og:image:alt" content="Festive dress">')
        self.assertNotContains(response, '<meta property="og:image" content="/static/shali/brand')

    @override_settings(ACCOUNT_PUBLIC_ORIGIN='https://shop.example', MEDIA_URL='https://cdn.example/')
    def test_product_sharing_preserves_cdn_photo_url_and_escapes_product_name(self):
        Product.objects.filter(pk=self.product.pk).update(product_name='Silk & "Gold" <Saree>')
        response = self.client.get(self.product.get_url())
        self.assertContains(response, '<meta property="og:image" content="https://cdn.example/photos/products/front.jpg">')
        self.assertContains(response, '<meta property="og:title" content="Silk &amp; &quot;Gold&quot; &lt;Saree&gt;">')

    def test_product_sharing_uses_next_photo_if_main_photo_is_missing(self):
        Product.objects.filter(pk=self.product.pk).update(image_1='')
        response = self.client.get(self.product.get_url())
        self.assertContains(response, '<meta property="og:image" content="http://testserver/media/photos/products/back.jpg">')

    def test_missing_images_and_zero_stock_render_without_add_action(self):
        Product.objects.filter(pk=self.product.pk).update(image_1='', image_2='', image_3='')
        ProductInventory.objects.filter(product=self.product, size='s').update(quantity=0)
        response = self.client.get(self.product.get_url())
        self.assertContains(response, 'Image coming soon')
        self.assertContains(response, 'Out of stock')
        self.assertNotContains(response, reverse('add_cart', args=[self.product.pk]))
        self.assertNotContains(response, 'property="og:image"')

    def test_free_size_and_unsized_products_do_not_require_size_selection(self):
        for size_type in ['free_size', 'no_size']:
            with self.subTest(size_type=size_type):
                Product.objects.filter(pk=self.product.pk).update(size_type=size_type)
                ProductInventory.objects.filter(product=self.product).delete()
                ProductInventory.objects.create(product=self.product, size=size_type, quantity=2)
                response = self.client.get(self.product.get_url())
                self.assertContains(response, 'Add to bag')
                self.assertNotContains(response, 'name="size"')
                self.assertRedirects(self.client.post(reverse('add_cart', args=[self.product.pk]), {'quantity': 1}), reverse('cart'))

    def test_hidden_products_and_wrong_catalog_paths_return_404(self):
        self.assertEqual(self.client.get('/store/product/men/clothing/festive-dress/').status_code, 404)
        self.assertEqual(self.client.get('/store/product/women/missing/festive-dress/').status_code, 404)
        self.assertEqual(self.client.get('/store/product/women/clothing/missing/').status_code, 404)
        Product.objects.filter(pk=self.product.pk).update(is_available=False)
        self.assertEqual(self.client.get(self.product.get_url()).status_code, 404)

    def test_homepage_and_catalog_link_to_product_details(self):
        for route in ['home', 'store:store']:
            with self.subTest(route=route):
                self.assertContains(self.client.get(reverse(route)), self.product.get_url())

    def test_unassigned_products_do_not_break_catalog_or_search(self):
        category = Category.objects.create(category_name='Unassigned', slug='unassigned')
        Product.objects.create(product_name='Unassigned dress', slug='unassigned-dress', category=category, color='Blue', price=1000)
        for route in ['store:store', 'store:search']:
            with self.subTest(route=route):
                response = self.client.get(reverse(route), {'keyword': 'dress'})
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, self.product.product_name)
                self.assertNotContains(response, 'Unassigned dress')


    def test_negative_price_is_rejected(self):
        self.product.price = -1
        with self.assertRaises(ValidationError):
            self.product.full_clean()


class ProductSubcategoryTests(TestCase):
    def setUp(self):
        self.department = Department.objects.create(
            department_name='Women',
            slug='women',
        )
        self.sarees = Category.objects.create(
            category_name='Sarees',
            slug='sarees',
            department=self.department,
        )
        self.jewellery = Category.objects.create(
            category_name='Jewellery',
            slug='jewellery',
            department=self.department,
        )
        self.banarasi = SubCategory.objects.create(
            category=self.sarees,
            subcategory_name='Banarasi',
            slug='banarasi',
        )
        self.cotton = SubCategory.objects.create(
            category=self.sarees,
            subcategory_name='Cotton',
            slug='cotton',
        )
        self.bangles = SubCategory.objects.create(
            category=self.jewellery,
            subcategory_name='Bangles',
            slug='bangles',
        )
        self.product = Product.objects.create(
            product_name='Silk Saree',
            slug='silk-saree',
            color='Red',
            price=5000,
            image_1='photos/products/silk-saree.jpg',
            size_type=Product.SizeType.CLOTHING,
            category=self.sarees,
        )

    def test_product_accepts_multiple_subcategories_from_its_category(self):
        self.product.subcategories.add(self.banarasi, self.cotton)

        self.assertQuerySetEqual(
            self.product.subcategories.order_by('slug'),
            [self.banarasi, self.cotton],
        )

    def test_product_rejects_subcategory_from_another_category(self):
        with self.assertRaises(ValidationError):
            self.product.subcategories.add(self.bangles)

    def test_subcategory_page_returns_assigned_product(self):
        self.product.subcategories.add(self.banarasi, self.cotton)

        response = self.client.get(reverse(
            'store:products_by_subcategory',
            args=['women', 'sarees', 'banarasi'],
        ))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.product_name)


class ProductInventoryTests(TestCase):
    def setUp(self):
        department = Department.objects.create(
            department_name='Women',
            slug='women',
        )
        category = Category.objects.create(
            category_name='Ethnic Wear',
            slug='ethnic-wear',
            department=department,
        )
        self.product = Product.objects.create(
            product_name='Festive Set',
            slug='festive-set',
            color='Blue',
            price=4000,
            image_1='photos/products/festive-set.jpg',
            size_type=Product.SizeType.CLOTHING,
            category=category,
        )

    def test_stock_is_tracked_independently_for_each_size(self):
        ProductInventory.objects.create(
            product=self.product,
            size=ProductInventory.Size.S,
            quantity=5,
        )
        out_of_stock_size = ProductInventory.objects.create(
            product=self.product,
            size=ProductInventory.Size.XL,
            quantity=0,
        )

        self.assertEqual(self.product.total_stock, 5)
        self.assertTrue(self.product.in_stock)
        self.assertFalse(out_of_stock_size.is_available)

    def test_clothing_product_rejects_free_size_inventory(self):
        inventory = ProductInventory(
            product=self.product,
            size=ProductInventory.Size.FREE_SIZE,
            quantity=2,
        )

        with self.assertRaises(ValidationError):
            inventory.full_clean()

class SearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        department = Department.objects.create(department_name='Women', slug='women')
        category = Category.objects.create(category_name='Sarees', slug='sarees', department=department)
        cls.products = []
        for number in range(14):
            cls.products.append(Product.objects.create(
                product_name=f'Silk saree {number:02d}', slug=f'silk-saree-{number}',
                description='Handwoven silk & cotton', category=category, price=1500, color='Red',
            ))
        Product.objects.filter(pk__in=[product.pk for product in cls.products]).update(
            create_date=cls.products[0].create_date,
        )
        cls.nonmatching = Product.objects.create(
            product_name='Wool shawl', slug='wool-shawl', category=category, price=1000, color='Blue',
        )
        for number, (name, description) in enumerate([
            ('Hidden silk saree', ''), ('Hidden shawl', 'Handwoven silk & cotton'),
        ]):
            Product.objects.create(
                product_name=name, slug=f'hidden-{number}', description=description,
                category=category, price=1000, color='Red', is_available=False,
            )

    def test_matches_names_or_descriptions_case_insensitively(self):
        for keyword in ['SAREE', 'HANDWOVEN', 'silk', '  silk  ']:
            with self.subTest(keyword=keyword):
                response = self.client.get(reverse('store:search'), {'keyword': keyword})

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context['keyword'], keyword.strip())
                self.assertEqual(response.context['product_count'], 14)
                self.assertEqual(list(response.context['products']), list(reversed(self.products))[:12])
                self.assertContains(response, self.products[-1].product_name)
                self.assertNotContains(response, self.nonmatching.product_name)
                self.assertNotContains(response, 'Hidden silk saree')
                self.assertNotContains(response, 'Hidden shawl')

    def test_empty_missing_and_unmatched_keywords(self):
        for keyword in [None, '', '   ', 'nonexistent']:
            with self.subTest(keyword=keyword):
                parameters = {} if keyword is None else {'keyword': keyword}
                response = self.client.get(reverse('store:search'), parameters)

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context['product_count'], 0)
                self.assertEqual(list(response.context['products']), [])
                self.assertNotContains(response, 'aria-label="Product pagination"')
                message = 'No products match your search.' if keyword == 'nonexistent' else 'Enter a keyword to search products.'
                self.assertContains(response, message)

    def test_pages_have_twelve_results_without_duplicates_or_omissions(self):
        result_ids = []
        for page_number, expected_count in [(1, 12), (2, 2)]:
            response = self.client.get(reverse('store:search'), {'keyword': 'silk', 'page': page_number})

            self.assertEqual(response.context['product_count'], 14)
            self.assertEqual(len(response.context['products']), expected_count)
            self.assertContains(response, f'Page {page_number} of 2')
            result_ids.extend(product.pk for product in response.context['products'])
        self.assertEqual(result_ids, [product.pk for product in reversed(self.products)])

    def test_newest_products_appear_first(self):
        Product.objects.filter(pk=self.products[0].pk).update(
            create_date=self.products[0].create_date + timedelta(days=1),
        )

        response = self.client.get(reverse('store:search'), {'keyword': 'silk'})

        self.assertEqual(response.context['products'][0], self.products[0])

    def test_missing_or_invalid_page_numbers(self):
        for page_value, expected_page in [(None, 1), ('', 1), ('abc', 1), ('1.5', 1), ('0', 2), ('-1', 2), ('999', 2)]:
            with self.subTest(page=page_value):
                parameters = {'keyword': 'silk'}
                if page_value is not None:
                    parameters['page'] = page_value
                response = self.client.get(reverse('store:search'), parameters)

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context['products'].number, expected_page)

    def test_pagination_preserves_encoded_keyword(self):
        first_page = self.client.get(reverse('store:search'), {'keyword': 'silk & cotton', 'page': 1})
        second_page = self.client.get(reverse('store:search'), {'keyword': 'silk & cotton', 'page': 2})

        self.assertContains(first_page, 'href="?keyword=silk+%26+cotton&amp;page=2" rel="next"')
        self.assertContains(second_page, 'href="?keyword=silk+%26+cotton&amp;page=1" rel="prev"')
        self.assertContains(second_page, 'value="silk &amp; cotton"')
        self.assertEqual(second_page.context['product_count'], 14)

    def test_twelve_results_fit_on_one_page(self):
        Product.objects.filter(pk__in=[product.pk for product in self.products[12:]]).delete()

        response = self.client.get(reverse('store:search'), {'keyword': 'silk'})

        self.assertEqual(response.context['product_count'], 12)
        self.assertEqual(len(response.context['products']), 12)
        self.assertNotContains(response, 'aria-label="Product pagination"')

    def test_keyword_is_escaped_in_results_and_form(self):
        keyword = '"><script>alert(1)</script>'

        response = self.client.get(reverse('store:search'), {'keyword': keyword})

        self.assertNotContains(response, '<script>alert(1)</script>')
        self.assertContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;')

    def test_search_forms_submit_keyword_to_search_route(self):
        for route in ['home', 'categories', 'store:store', 'store:search']:
            with self.subTest(route=route):
                response = self.client.get(reverse(route))

                self.assertContains(response, 'role="search" action="/store/search/" method="get"')
                self.assertContains(response, 'type="search" name="keyword"')
                self.assertNotContains(response, 'Product search is coming soon.')


class StorePaginationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        department = Department.objects.create(department_name='Women', slug='women')
        other_department = Department.objects.create(department_name='Men', slug='men')
        category = Category.objects.create(category_name='Sarees', slug='sarees', department=department)
        other_category = Category.objects.create(category_name='Sets', slug='sets', department=department)
        mens_category = Category.objects.create(category_name='Shirts', slug='shirts', department=other_department)
        subcategory = SubCategory.objects.create(category=category, subcategory_name='Silk', slug='silk')
        cls.products = []
        for number in range(14):
            product = Product.objects.create(
                product_name=f'Silk saree {number:02d}', slug=f'silk-saree-{number}',
                category=category, price=1500, color='Red',
            )
            product.subcategories.add(subcategory)
            cls.products.append(product)
        cls.other_products = []
        for number, product_category in enumerate([category, other_category, mens_category]):
            cls.other_products.append(Product.objects.create(
                product_name=f'Other product {number}', slug=f'other-product-{number}',
                category=product_category, price=1000, color='Blue',
            ))
        hidden = Product.objects.create(
            product_name='Hidden product', slug='hidden-product', category=category,
            price=1000, color='Red', is_available=False,
        )
        hidden.subcategories.add(subcategory)
        cls.routes = [
            (reverse('store:store'), cls.products + cls.other_products),
            (department.get_url(), cls.products + cls.other_products[:2]),
            (category.get_url(), cls.products + cls.other_products[:1]),
            (subcategory.get_url(), cls.products),
        ]

    def test_all_catalog_routes_filter_before_paginating(self):
        for route, expected_products in self.routes:
            for page_number in [1, 2]:
                with self.subTest(route=route, page=page_number):
                    response = self.client.get(route, {'page': page_number})
                    start = (page_number - 1) * 12

                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.context['product_count'], len(expected_products))
                    self.assertEqual(list(response.context['products']), expected_products[start:start + 12])
                    self.assertContains(response, f'Page {page_number} of 2')
                    self.assertNotContains(response, 'Hidden product')
                    for product in expected_products[start:start + 12]:
                        self.assertContains(response, product.product_name)
                    for product in expected_products[:start] + expected_products[start + 12:]:
                        self.assertNotContains(response, product.product_name)

    def test_missing_or_invalid_page_numbers_are_handled(self):
        for page_value, expected_page in [(None, 1), ('', 1), ('abc', 1), ('1.5', 1), ('0', 2), ('-1', 2), ('999', 2)]:
            with self.subTest(page=page_value):
                parameters = {} if page_value is None else {'page': page_value}
                response = self.client.get(reverse('store:store'), parameters)

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context['products'].number, expected_page)

    def test_navigation_keeps_query_parameters_and_catalog_path(self):
        route = self.routes[-1][0]
        first_page = self.client.get(route, {'size': ['s', 'xl'], 'page': 1})
        second_page = self.client.get(route, {'size': ['s', 'xl'], 'page': 2})

        self.assertContains(first_page, 'href="?size=s&amp;size=xl&amp;page=2" rel="next"')
        self.assertNotContains(first_page, 'rel="prev"')
        self.assertContains(second_page, 'href="?size=s&amp;size=xl&amp;page=1" rel="prev"')
        self.assertNotContains(second_page, 'rel="next"')
        self.assertEqual(second_page.context['selected_subcategory'].slug, 'silk')

    def test_empty_catalog_has_no_pagination_controls(self):
        Product.objects.all().delete()

        response = self.client.get(reverse('store:store'), {'page': 99})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['product_count'], 0)
        self.assertEqual(list(response.context['products']), [])
        self.assertContains(response, 'No products are available.')
        self.assertNotContains(response, 'aria-label="Product pagination"')

    def test_single_page_has_no_pagination_controls(self):
        Product.objects.exclude(pk__in=[product.pk for product in self.products[:12]]).delete()

        response = self.client.get(reverse('store:store'))

        self.assertEqual(response.context['product_count'], 12)
        self.assertEqual(len(response.context['products']), 12)
        self.assertNotContains(response, 'aria-label="Product pagination"')
