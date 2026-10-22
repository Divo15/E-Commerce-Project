from django.urls import path
from . import views
from orders.whatsapp import buy_bag



urlpatterns = [
    path('buy/', buy_bag, name='buy_bag'),
    path('', views.cart, name='cart'),
    path('add_cart/<int:product_id>', views.add_cart, name='add_cart'),
    path('items/<int:item_id>/update/', views.update_cart, name='update_cart'),
    path('items/<int:item_id>/increase/', views.increase_cart, name='increase_cart'),
    path('items/<int:item_id>/decrease/', views.decrease_cart, name='decrease_cart'),
    path('items/<int:item_id>/remove/', views.remove_cart, name='remove_cart'),
]
