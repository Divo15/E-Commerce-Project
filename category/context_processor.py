from django.db.models import Prefetch

from .models import Category, Department


def menu_links(request):
    links = Category.objects.select_related('department').order_by('pk')
    navigation_categories = Category.objects.order_by('pk').prefetch_related('subcategories')
    departments = Department.objects.order_by('pk').prefetch_related(
        Prefetch('categories', queryset=navigation_categories),
    )
    return {'links': links, 'departments': departments}
