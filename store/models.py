from django.db import models
from django.core.exceptions import ValidationError
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from category.models import Category, SubCategory
from django.urls import reverse

# Create your models here.
class Product(models.Model):
    product_name = models.CharField(max_length=200, unique = True)
    slug = models.SlugField(max_length=200, unique= True)
    description = models.TextField(max_length=500, blank = True)
    color = models.CharField(max_length=50)
    price  = models.IntegerField()
    images = models.ImageField(upload_to='photos/products')
    stock = models.BooleanField(default=False)
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


    def __str__(self):
        return self.product_name 


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


