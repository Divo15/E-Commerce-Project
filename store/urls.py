from django.urls import path
from . import views
from orders.whatsapp import buy_now

app_name = 'store'

urlpatterns = [
    path('buy/<int:product_id>/', buy_now, name='buy_now'),
    path('',views.store, name='store'),
    path(
        'category/<slug:department_slug>/',
        views.store,
        name='products_by_department',
    ),
    path(
        'category/<slug:department_slug>/<slug:category_slug>/',
        views.store,
        name='products_by_category',
    ),
    path(
        'category/<slug:department_slug>/<slug:category_slug>/<slug:subcategory_slug>/',
        views.store,
        name='products_by_subcategory',
    ),
    path(
        'product/<slug:department_slug>/<slug:category_slug>/<slug:product_slug>/',
        views.product_detail,
        name='product_detail',
    ),
    path('search/', views.search, name='search'),
]
