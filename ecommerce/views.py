from django.shortcuts import render
from django.db.models import Prefetch
from category.models import Category, HeroPoster
from store.models import Product

def home(request):
    categories = list(Category.objects.filter(
        department__isnull=False,
    ).select_related('department').prefetch_related(Prefetch(
        'product_set',
        queryset=Product.objects.filter(is_available=True).select_related(
            'category__department',
        ).order_by('-create_date', '-pk')[:8],
        to_attr='home_products',
    )).order_by('pk'))
    illustrated_categories = [category for category in categories if category.category_image]
    hero_category = next(
        (category for category in illustrated_categories if category.slug.lower() == 'sarees'),
        illustrated_categories[0] if illustrated_categories else None,
    )
    category_priority = {'sarees': 0, 'churidar': 1, 'shirts': 2}
    product_rows = sorted(
        (category for category in categories if category.home_products),
        key=lambda category: category_priority.get(category.slug.lower(), 3),
    )
    mobile_categories = []
    if hero_category:
        mobile_categories.append(hero_category)
    mobile_departments = {
        category.department_id for category in mobile_categories
    }
    for category in illustrated_categories:
        if len(mobile_categories) == 4:
            break
        if category not in mobile_categories and category.department_id not in mobile_departments:
            mobile_categories.append(category)
            mobile_departments.add(category.department_id)
    for category in illustrated_categories:
        if len(mobile_categories) == 4:
            break
        if category not in mobile_categories:
            mobile_categories.append(category)
    hero_posters = list(HeroPoster.objects.exclude(image='')[:3])
    context = {
        'product_rows': product_rows,
        'home_categories': categories,
        'hero_category': hero_category,
        'hero_poster': hero_posters[0] if hero_posters else None,
        'hero_posters': hero_posters,
        'mobile_categories': mobile_categories,
    }
    return render(request,'home.html',context)


def categories(request):
    return render(request, 'categories.html')


def store(request):
    return render(request, 'store/store.html')
