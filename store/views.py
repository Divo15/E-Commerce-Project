from django.shortcuts import render,get_object_or_404
from category.models import Category, Department, SubCategory
from . models import Product


def store(
    request,
    department_slug=None,
    category_slug=None,
    subcategory_slug=None,
):
    department = None
    category = None
    subcategory = None

    products = Product.objects.filter(is_available=True)

    if department_slug is not None:
        department = get_object_or_404(Department, slug=department_slug)
        products = products.filter(category__department=department)

    if category_slug is not None:
        category = get_object_or_404(
            Category,
            department=department,
            slug=category_slug,
        )
        products = products.filter(category=category)

    if subcategory_slug is not None:
        subcategory = get_object_or_404(
            SubCategory,
            category=category,
            slug=subcategory_slug,
        )
        products = products.filter(subcategories=subcategory)

    context = {
        'products': products,
        'product_count': products.count(),
        'selected_department': department,
        'selected_category': category,
        'selected_subcategory': subcategory,
    }
    return render(request,'store/store.html',context)

def product_detail(request, department_slug, category_slug, product_slug):
    single_product = get_object_or_404(
        Product,
        category__department__slug=department_slug,
        category__slug=category_slug,
        slug=product_slug,
        is_available=True,
    )
    context = {
        'single_product': single_product,
    }
    return render(request, 'store/product_detail.html',context)





# Create your views here.
