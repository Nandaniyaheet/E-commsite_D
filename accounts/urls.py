from accounts.views import (
    activate_email,
    add_to_cart,
    cart,
    login_page,
    register_page,
    remove_coupon,
    remove_from_cart,
    update_cart_item,
)
from django.urls import path


urlpatterns = [
   path('login/' , login_page , name="login" ),
   path('register/' , register_page , name="register"),
   path('activate/<email_token>/' , activate_email , name="activate_email"),
   path('cart/' , cart , name="cart"),
   path('add-to-cart/<uid>/', add_to_cart, name="add_to_cart"),
   path('cart-item/<cart_item_uid>/update/', update_cart_item, name="update_cart_item"),
   path('remove-cart/<cart_item_uid>/', remove_from_cart, name="remove_cart"),
   path('remove-coupon/<cart_id>/', remove_coupon, name="remove_coupon"),
]
