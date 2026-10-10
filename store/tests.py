from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from category.models import Category, Department, SubCategory

from .models import Product, ProductInventory


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

# Create your tests here.
