from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import Sum
from django.contrib.auth.models import User
from base.models import BaseModel
from django.db.models.signals import post_save
from django.dispatch import receiver
from product.models import Coupon, Product, ColorVariant, SizeVariant  # Add this import for Coupon_
import uuid


class Profile(BaseModel):
    user = models.OneToOneField(User , on_delete=models.CASCADE , related_name="profile")
    is_email_verified = models.BooleanField(default=False)
    email_token = models.CharField(max_length=100 , null=True , blank=True)
    profile_image = models.ImageField(upload_to = 'profile')

    def get_cart_count(self):
        quantity = CartItem.objects.filter(
            cart__is_paid=False,
            cart__user=self.user,
        ).aggregate(total=Sum('quantity'))['total']
        return quantity or 0
    
class Cart(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cart")
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True, related_name="carts")
    is_paid = models.BooleanField(default=False)
  
    
    def get_cart_subtotal(self):
        return sum(
            item.get_product_price() * item.quantity
            for item in self.cart_items.select_related(
                "product", "color_variant", "size_variant"
            )
        )

    def get_cart_total(self):
        subtotal = self.get_cart_subtotal()
        if self.coupon:
            return self.coupon.get_discounted_price(subtotal)
        return subtotal

class CartItem(BaseModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="cart_items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name="cart_items")
    color_variant = models.ForeignKey(ColorVariant, on_delete=models.SET_NULL, null=True, blank=True, related_name="cart_items")
    size_variant = models.ForeignKey(SizeVariant, on_delete=models.SET_NULL, null=True, blank=True, related_name="cart_items")
    quantity = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(99)],
    )

    def get_product_price(self):
        if self.product is None:
            return 0

        price = [self.product.price]
        if self.color_variant:
            price.append(self.color_variant.price)
        if self.size_variant:
            price.append(self.size_variant.price)
        return sum(price)

@receiver(post_save , sender = User)
def send_email_token(sender, instance, created, raw=False, **kwargs):
    if created and not raw:
        Profile.objects.create(user=instance, email_token=str(uuid.uuid4()))