from django.db import models
from django.core.exceptions import ValidationError
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from category.models import Category, SubCategory
from django.urls import reverse

# Create your models here.
class Product(models.Model):
    class SizeType(models.TextChoices):
        NO_SIZE = 'no_size', 'No size'
        CLOTHING = 'clothing', 'Clothing sizes'
        FREE_SIZE = 'free_size', 'Free size'

    product_name = models.CharField(max_length=200, unique = True)
    slug = models.SlugField(max_length=200, unique= True)
    description = models.TextField(max_length=500, blank = True)
    color = models.CharField(max_length=50)
    price  = models.IntegerField()
    images = models.ImageField(upload_to='photos/products')
    size_type = models.CharField(
        max_length=20,
        choices=SizeType.choices,
        default=SizeType.NO_SIZE,
    )
    is_available = models.BooleanField(default=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    subcategories = models.ManyToManyField(
        SubCategory,
        blank=True,
        related_name='products',
    )
    create_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    def get_url(self):
        return reverse(
            'store:product_detail',
            args=[self.category.department.slug, self.category.slug, self.slug],
        )

    @property
    def total_stock(self):
        return self.inventory.aggregate(total=models.Sum('quantity'))['total'] or 0

    @property
    def in_stock(self):
        return self.total_stock > 0


    def __str__(self):
        return self.product_name 


class ProductInventory(models.Model):
    class Size(models.TextChoices):
        NO_SIZE = 'no_size', 'No size'
        S = 's', 'S'
        XL = 'xl', 'XL'
        XXL = 'xxl', 'XXL'
        FREE_SIZE = 'free_size', 'Free Size'

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='inventory',
    )
    size = models.CharField(max_length=20, choices=Size.choices)
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'product inventory'
        verbose_name_plural = 'product inventory'
        constraints = [
            models.UniqueConstraint(
                fields=('product', 'size'),
                name='unique_size_per_product',
            ),
        ]

    def clean(self):
        super().clean()

        allowed_sizes = {
            Product.SizeType.NO_SIZE: {self.Size.NO_SIZE},
            Product.SizeType.CLOTHING: {self.Size.S, self.Size.XL, self.Size.XXL},
            Product.SizeType.FREE_SIZE: {self.Size.FREE_SIZE},
        }

        if self.product and self.size not in allowed_sizes[self.product.size_type]:
            raise ValidationError({
                'size': 'This size is not valid for the product size type.',
            })

    @property
    def is_available(self):
        return self.quantity > 0

    def __str__(self):
        return f'{self.product} - {self.get_size_display()}: {self.quantity}'


@receiver(m2m_changed, sender=Product.subcategories.through)
def validate_product_subcategories(sender, instance, action, reverse, pk_set, **kwargs):
    if action != 'pre_add' or not pk_set:
        return

    if reverse:
        has_invalid_product = Product.objects.filter(pk__in=pk_set).exclude(
            category_id=instance.category_id,
        ).exists()
    else:
        has_invalid_product = SubCategory.objects.filter(pk__in=pk_set).exclude(
            category_id=instance.category_id,
        ).exists()

    if has_invalid_product:
        raise ValidationError(
            'Every selected subcategory must belong to the product category.'
        )


