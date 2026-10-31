from accounts.models import Cart

def cart_item_count(request):
    count = 0
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            count = cart.cart_items.count() # Change if you used a related_name
        except Cart.DoesNotExist:
            pass
    return {'cart_item_count': count}