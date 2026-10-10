from django.db import models
from django.urls import reverse

# Create your models here.
class Department(models.Model):
    department_name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        verbose_name = 'department'
        verbose_name_plural = 'departments'

    def get_url(self):
        return reverse('store:products_by_department', args=[self.slug])

    def __str__(self):
        return self.department_name


class Category(models.Model):
    category_name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(max_length=100, blank=True)
    category_image = models.ImageField(upload_to='photos/categories', blank=True)
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='categories',
        blank=True,
        null=True,
    )


    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'


    def get_url(self):
        return reverse(
            'store:products_by_category',
            args=[self.department.slug, self.slug],
        )


    def __str__(self):
        return self.category_name

class SubCategory(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='subcategories',
    )
    subcategory_name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)
    description = models.TextField(max_length=500, blank=True)

    class Meta:
        verbose_name = 'sub-category'
        verbose_name_plural = 'sub-categories'
        constraints = [
            models.UniqueConstraint(
                fields=['category', 'slug'],
                name='unique_subcategory_slug_per_category',
            )
        ]

    def get_url(self):
        return reverse(
            'store:products_by_subcategory',
            args=[self.category.department.slug, self.category.slug, self.slug],
        )

    def __str__(self):
        return f'{self.category} - {self.subcategory_name}'


class HeroPoster(models.Model):
    image = models.ImageField(upload_to='photos/hero')
    alt_text = models.CharField(max_length=200)

    class Meta:
        verbose_name = 'hero poster'
        verbose_name_plural = 'hero posters'
        ordering = ('-pk',)

    def __str__(self):
        return 'Homepage hero poster'
