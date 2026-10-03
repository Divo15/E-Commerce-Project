from django.contrib import admin
from .models import Category, Department, SubCategory


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
