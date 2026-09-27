from django import forms
from django.contrib import admin
from . models import Product


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        subcategories = cleaned_data.get('subcategories')

        if (
            category
            and subcategories
            and subcategories.exclude(category=category).exists()
        ):
            self.add_error(
                'subcategories',
                'Every selected subcategory must belong to the product category.',
            )

        return cleaned_data


class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = (
        'product_name',
        'price',
        'stock',
        'category',
        'subcategory_list',
        'modified_date',
        'color',
        'is_available',
    )
    prepopulated_fields = {'slug':('product_name',)}
    filter_horizontal = ('subcategories',)

    @admin.display(description='Subcategories')
    def subcategory_list(self, product):
        return ', '.join(
            product.subcategories.values_list('subcategory_name', flat=True)
        ) or '-'

admin.site.register(Product, ProductAdmin)


# Register your models here.
