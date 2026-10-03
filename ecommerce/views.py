from django.shortcuts import render
from category.models import Category
from store.models import Product

def home(request):
    categories = list(Category.objects.filter(
        department__isnull=False,
    ).select_related('department').order_by('pk'))
    illustrated_categories = [category for category in categories if category.category_image]
    hero_category = next(
        (category for category in illustrated_categories if category.slug.lower() == 'sarees'),
        illustrated_categories[0] if illustrated_categories else None,
    )
    featured_categories = []
    featured_departments = set()
    for category in illustrated_categories:
        if category.department_id not in featured_departments and category != hero_category:
            featured_categories.append(category)
            featured_departments.add(category.department_id)
    products = Product.objects.filter(
        is_available=True,
        category__department__isnull=False,
    ).select_related('category__department').order_by('-create_date', '-pk')[:4]

    context = {
        'products': products,
        'home_categories': categories,
        'hero_category': hero_category,
        'featured_categories': featured_categories[:3],
    }
    return render(request,'home.html',context)


def categories(request):
    return render(request, 'categories.html')


def store(request):
    return render(request, 'store/store.html')
