from django.test import TestCase
from django.urls import reverse

from category.models import Category, Department, HeroPoster, SubCategory
from store.models import Product


class HomepageTests(TestCase):
    def test_hero_falls_back_to_campaign_without_uploaded_poster(self):
        response = self.client.get(reverse('home'))

        self.assertIsNone(response.context['hero_poster'])
        self.assertContains(response, '/static/shali/hero-campaign.webp')
        self.assertNotContains(response, 'landing-hero-poster')

    def test_hero_uses_newest_uploaded_poster_and_its_alt_text(self):
        department = Department.objects.create(department_name='Women', slug='women')
        Category.objects.create(category_name='Sarees', slug='sarees', department=department, category_image='sarees.jpg')
        older_poster = HeroPoster.objects.create(
            image='photos/hero/older.jpg',
            alt_text='Previous collection',
        )
        newest_poster = HeroPoster.objects.create(
            image='photos/hero/newest.jpg',
            alt_text='Our festive collection',
        )
        HeroPoster.objects.create(image='', alt_text='Missing image')

        response = self.client.get(reverse('home'))

        self.assertEqual(response.context['hero_poster'], newest_poster)
        self.assertContains(response, newest_poster.image.url)
        self.assertContains(response, 'alt="Our festive collection"')
        self.assertContains(response, 'landing-hero-poster')
        self.assertNotContains(response, 'landing-hero-detail')
        self.assertNotContains(response, older_poster.image.url)
        self.assertNotContains(response, '/static/shali/hero-campaign.webp')

    def test_department_navigation_does_not_leak_other_department_products(self):
        for department_name in ['Women', 'Men']:
            department = Department.objects.create(department_name=department_name, slug=department_name.lower())
            category = Category.objects.create(category_name=department_name, slug=department_name.lower(), department=department)
            Product.objects.create(product_name=f'{department_name} outfit', slug=f'{department_name.lower()}-outfit', price=1500, color='Red', category=category)

        response = self.client.get(reverse('store:products_by_department', args=['women']))

        self.assertContains(response, 'Women outfit')
        self.assertNotContains(response, 'Men outfit')

    def test_empty_catalog_renders_brand_and_useful_empty_state(self):
        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Shali Collections')
        self.assertContains(response, 'Something lovely is on its way.')
        self.assertContains(response, '/static/shali/brand.jpg')
        self.assertEqual(response.context['home_categories'], [])

    def test_navigation_contains_complete_catalog_paths(self):
        department = Department.objects.create(department_name='Women', slug='women')
        category = Category.objects.create(category_name='Sarees', slug='sarees', department=department)
        subcategory = SubCategory.objects.create(category=category, subcategory_name='Banarasi', slug='banarasi')

        for route in ['home', 'categories']:
            with self.subTest(route=route):
                response = self.client.get(reverse(route))
                self.assertEqual(response.status_code, 200)
                for entry in [department, category, subcategory]:
                    self.assertContains(response, entry.get_url())

    def test_categories_without_departments_do_not_break_homepage(self):
        Category.objects.create(category_name='Unassigned', slug='unassigned')

        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['home_categories'], [])

    def test_hero_uses_saree_image_and_falls_back_to_other_category(self):
        department = Department.objects.create(department_name='Women', slug='women')
        other = Category.objects.create(category_name='Sets', slug='sets', department=department, category_image='sets.jpg')
        sarees = Category.objects.create(category_name='Sarees', slug='sarees', department=department, category_image='sarees.jpg')

        self.assertEqual(self.client.get(reverse('home')).context['hero_category'], sarees)
        sarees.delete()
        self.assertEqual(self.client.get(reverse('home')).context['hero_category'], other)

    def test_mobile_categories_prioritize_hero_and_department_variety(self):
        women = Department.objects.create(department_name='Women', slug='women')
        jewellery = Department.objects.create(department_name='Jewellery', slug='jewellery')
        men = Department.objects.create(department_name='Men', slug='men')
        dresses = Category.objects.create(category_name='Dresses', slug='dresses', department=women, category_image='dresses.jpg')
        sarees = Category.objects.create(category_name='Sarees', slug='sarees', department=women, category_image='sarees.jpg')
        necklaces = Category.objects.create(category_name='Necklaces', slug='necklaces', department=jewellery, category_image='necklaces.jpg')
        shirts = Category.objects.create(category_name='Shirts', slug='shirts', department=men, category_image='shirts.jpg')

        response = self.client.get(reverse('home'))

        self.assertEqual(response.context['mobile_categories'], [sarees, necklaces, shirts, dresses])
        self.assertContains(response, 'landing-mobile-categories')

    def test_product_rows_keep_categories_separate_and_include_new_shirts(self):
        women = Department.objects.create(department_name='Women', slug='women')
        men = Department.objects.create(department_name='Men', slug='men')
        churidar = Category.objects.create(category_name='Churidar', slug='Churidar', department=women, category_image='churidar.jpg')
        sarees = Category.objects.create(category_name='Sarees', slug='sarees', department=women, category_image='sarees.jpg')
        shirts = Category.objects.create(category_name='Shirts', slug='shirts', department=men)
        for category in [sarees, churidar]:
            Product.objects.create(product_name=f'{category.category_name} piece', slug=f'{category.slug.lower()}-piece', price=1500, color='Red', category=category)

        self.assertEqual([row.pk for row in self.client.get(reverse('home')).context['product_rows']], [sarees.pk, churidar.pk])
        Product.objects.create(product_name='Cotton shirt', slug='cotton-shirt', price=1200, color='White', category=shirts)

        response = self.client.get(reverse('home'))

        self.assertEqual([row.pk for row in response.context['product_rows']], [sarees.pk, churidar.pk, shirts.pk])
        for row in response.context['product_rows']:
            self.assertTrue(all(product.category_id == row.pk for product in row.home_products))
            self.assertContains(response, f'aria-label="{row.category_name} products"')

    def test_new_arrivals_show_only_available_products_with_complete_paths(self):
        department = Department.objects.create(department_name='Women', slug='women')
        category = Category.objects.create(category_name='Sarees', slug='sarees', department=department)
        unassigned = Category.objects.create(category_name='Unassigned', slug='unassigned')
        for number in range(10):
            Product.objects.create(product_name=f'Available {number}', slug=f'available-{number}', price=1500, color='Red', category=category, image_1='')
        Product.objects.create(product_name='Hidden', slug='hidden', price=1500, color='Red', category=category, is_available=False)
        Product.objects.create(product_name='Unassigned product', slug='unassigned-product', price=1500, color='Red', category=unassigned)

        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['product_rows']), 1)
        self.assertEqual([product.product_name for product in response.context['product_rows'][0].home_products], [f'Available {number}' for number in range(9, 1, -1)])
        self.assertNotContains(response, 'Unassigned product')
        self.assertNotContains(response, '>Hidden<')
        self.assertContains(response, 'Image coming soon')
