from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from base.emails import send_account_activation_email
from .forms import AddToCartForm, CartQuantityForm
from .models import Cart, CartItem, Profile
from product.models import Coupon, Product


def login_page(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        user_obj = User.objects.filter(username__iexact=email).first()

        if user_obj is None:
            messages.warning(request, 'Account not found.')
            return redirect(request.path_info)

        profile = Profile.objects.filter(user=user_obj).first()
        if profile is None or not profile.is_email_verified:
            messages.warning(request, 'Your account is not verified.')
            return redirect(request.path_info)

        authenticated_user = authenticate(username=user_obj.username, password=password)
        if authenticated_user:
            login(request, authenticated_user)
            return redirect('/')

        messages.warning(request, 'Invalid credentials')
        return redirect(request.path_info)

    return render(request, 'accounts/login.html')


def register_page(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        try:
            validate_email(email)
        except ValidationError:
            messages.warning(request, 'Enter a valid email address.')
            return redirect(request.path_info)

        user_obj = User.objects.filter(username__iexact=email)

        if user_obj.exists():
            messages.warning(request, 'Email is already taken.')
            return redirect(request.path_info)

        user = User(first_name=first_name, last_name=last_name, email=email, username=email)
        try:
            validate_password(password, user=user)
        except ValidationError as error:
            for message in error.messages:
                messages.warning(request, message)
            return redirect(request.path_info)

        with transaction.atomic():
            user.set_password(password)
            user.save()
            send_account_activation_email(user.email, user.profile.email_token)
        messages.success(request, 'An email has been sent on your mail.')
        return redirect(request.path_info)

    return render(request, 'accounts/register.html')


def activate_email(request, email_token):
    profile = get_object_or_404(Profile, email_token=email_token, is_email_verified=False)
    profile.is_email_verified = True
    profile.email_token = ''
    profile.save(update_fields=['is_email_verified', 'email_token'])
    return redirect('/')


@login_required
@require_POST
def add_to_cart(request, uid):
    product = get_object_or_404(Product, uid=uid)
    form = AddToCartForm(request.POST)
    if not form.is_valid():
        messages.warning(request, 'Choose a quantity between 1 and 99.')
        return redirect('get_products', slug=product.slug)

    size_variant = None
    if product.size_variant.exists():
        size_variant = product.size_variant.filter(
            size_name=form.cleaned_data['variant']
        ).first()
        if size_variant is None:
            messages.warning(request, 'Choose a valid size.')
            return redirect('get_products', slug=product.slug)

    color_variant = None
    if product.color_variant.exists():
        color_variant = product.color_variant.filter(
            uid=form.cleaned_data['color_variant']
        ).first()
        if color_variant is None:
            messages.warning(request, 'Choose a valid color.')
            return redirect('get_products', slug=product.slug)

    cart, _ = Cart.objects.get_or_create(user=request.user, is_paid=False)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        size_variant=size_variant,
        color_variant=color_variant,
        defaults={'quantity': form.cleaned_data['quantity']},
    )
    if not created:
        quantity = cart_item.quantity + form.cleaned_data['quantity']
        if quantity > 99:
            messages.warning(request, 'A cart item cannot exceed 99 units.')
            return redirect('get_products', slug=product.slug)
        cart_item.quantity = quantity
        cart_item.save(update_fields=['quantity'])

    messages.success(request, 'Item added to cart.')
    return redirect('get_products', slug=product.slug)


@login_required
@require_POST
def update_cart_item(request, cart_item_uid):
    cart_item = get_object_or_404(
        CartItem,
        uid=cart_item_uid,
        cart__user=request.user,
        cart__is_paid=False,
    )
    form = CartQuantityForm(request.POST)
    if not form.is_valid():
        messages.warning(request, 'Choose a quantity between 1 and 99.')
        return redirect('cart')
    cart_item.quantity = form.cleaned_data['quantity']
    cart_item.save(update_fields=['quantity'])
    return redirect('cart')


@login_required
@require_POST
def remove_from_cart(request, cart_item_uid):
    cart_item = get_object_or_404(
        CartItem,
        uid=cart_item_uid,
        cart__user=request.user,
        cart__is_paid=False,
    )
    cart_item.delete()
    messages.success(request, 'Item removed from cart.')
    return redirect('cart')


@login_required
def cart(request):
    cart_obj, _ = Cart.objects.get_or_create(user=request.user, is_paid=False)

    if request.method == 'POST':
        coupon_code = request.POST.get('coupon', '').strip()
        coupon = Coupon.objects.filter(
            coupon_code__iexact=coupon_code,
            is_expired=False,
        ).first()
        if coupon is None:
            messages.warning(request, 'Invalid coupon code.')
            return redirect('cart')

        if cart_obj.coupon:
            messages.warning(request, 'You have already applied a coupon. or Coupon is already exists.')
            return redirect('cart')

        if cart_obj.get_cart_total() < coupon.minimum_amount:
            messages.warning(request, f'Amount should be at least {coupon.minimum_amount}.')
            return redirect('cart')

        cart_obj.coupon = coupon
        cart_obj.save()
        messages.success(request, 'Coupon applied successfully.')
        return redirect('cart')

    total_price = cart_obj.get_cart_total()
    discount = cart_obj.get_cart_subtotal() - total_price

    context = {
        'cart': cart_obj,
        'total_price': total_price,
        'discount': discount,
        'quantity_range': range(1, 100),
    }
    return render(request, 'accounts/cart.html', context)


@login_required
@require_POST
def remove_coupon(request, cart_id):
    cart = get_object_or_404(
        Cart,
        uid=cart_id,
        user=request.user,
        is_paid=False,
    )
    cart.coupon = None
    cart.save()
    messages.success(request, 'Coupon removed successfully.')
    return redirect('cart')