from django.urls import path

from . import views


app_name = 'orders'

urlpatterns = [
    path('shipping/', views.shipping_details, name='shipping_details'),
    path('shipping/review/', views.shipping_review, name='shipping_review'),
]
