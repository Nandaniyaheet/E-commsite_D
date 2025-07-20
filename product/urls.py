from django.urls import path, include
from product.views import get_products

urlpatterns = [
    path('<slug:slug>/', get_products, name='get_products'),    
]