from django.db.models import Sum
from accounts.models import CartItem

def cart_item_count(request):
    if not request.user.is_authenticated:
        return {'cart_item_count': 0}

    quantity = CartItem.objects.filter(
        cart__user=request.user,
        cart__is_paid=False,
    ).aggregate(total=Sum('quantity'))['total']
    return {'cart_item_count': quantity or 0}