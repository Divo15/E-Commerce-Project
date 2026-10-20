from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from carts.forms import AddCartForm
from category.models import Category, Department, SubCategory
from . models import Product
from django.db.models import Q


def _add_stock_context(product):
    allowed_sizes = dict(AddCartForm(product=product).fields['size'].choices)
    product.stocked_inventory = [
        row for row in product.inventory.all()
        if row.size in allowed_sizes and row.quantity > 0
    ]
    product.available_stock = sum(row.quantity for row in product.stocked_inventory)
    return product


def store(
    request,
    department_slug=None,
    category_slug=None,
    subcategory_slug=None,
):
    department = None
    category = None
    subcategory = None

    products = Product.objects.filter(is_available=True, category__department__isnull=False)

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

    products = products.select_related('category__department').prefetch_related('inventory').order_by('pk')
    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(request.GET.get('page'))
    for product in page_obj:
        _add_stock_context(product)

    context = {
        'products': page_obj,
        'product_count': paginator.count,
        'selected_department': department,
        'selected_category': category,
        'selected_subcategory': subcategory,
    }
    return render(request,'store/store.html',context)

def product_detail(request, department_slug, category_slug, product_slug):
    single_product = get_object_or_404(
        Product.objects.select_related('category__department').prefetch_related('inventory'),
        category__department__slug=department_slug,
        category__slug=category_slug,
        slug=product_slug,
        is_available=True,
    )
    _add_stock_context(single_product)
    context = {
        'single_product': single_product,
        'stocked_inventory': single_product.stocked_inventory,
        'available_stock': single_product.available_stock,
        'product_images': [
            image for image in (single_product.image_1, single_product.image_2, single_product.image_3)
            if image
        ],
    }
    return render(request, 'store/product_detail.html',context)


def search(request):
    keyword = request.GET.get('keyword', '').strip()
    products = Product.objects.none()
    if keyword:
        products = Product.objects.filter(
            Q(description__icontains=keyword) | Q(product_name__icontains=keyword),
            is_available=True,
            category__department__isnull=False,
        ).select_related('category__department').prefetch_related('inventory').order_by('-create_date', '-pk')
    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(request.GET.get('page'))
    for product in page_obj:
        _add_stock_context(product)
    context = {
        'products': page_obj,
        'product_count': paginator.count,
        'keyword': keyword,
        'is_search': True,
    }
    return render(request, 'store/store.html', context)





# Create your views here.
