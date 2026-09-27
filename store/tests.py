from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from category.models import Category, Department, SubCategory

from .models import Product


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
            images='photos/products/silk-saree.jpg',
            stock=True,
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

# Create your tests here.
