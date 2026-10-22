from django.contrib import admin
from .models import Category, Department, HeroPoster, SubCategory


@admin.register(HeroPoster)
class HeroPosterAdmin(admin.ModelAdmin):
    list_display = ('alt_text', 'image')

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['image'].help_text = (
            'Add one image per hero poster. The homepage cycles through the three '
            'most recently added posters, newest first. Use images with matching '
            'dimensions for a consistent slideshow.'
        )
        return form


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('department_name', 'slug')
    prepopulated_fields = {'slug': ('department_name',)}


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('category_name', 'department', 'slug')
    list_filter = ('department',)
    prepopulated_fields = {'slug': ('category_name',)}
    exclude = ('description',)

@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = (
        'subcategory_name',
        'category',
        'slug',
    )
    list_filter = ('category',)
    prepopulated_fields = {
        'slug': ('subcategory_name',),
    }
    exclude = ('description',)
