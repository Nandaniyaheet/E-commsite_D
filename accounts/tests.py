from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from accounts.models import Cart, CartItem
from base.emails import send_account_activation_email
from product.models import Category, ColorVariant, Coupon, Product, SizeVariant


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class CartAuthenticationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='buyer@example.com',
            email='buyer@example.com',
            password='Secure-test-password-42',
        )
        self.category = Category.objects.create(
            category_name='Test category',
            category_image='categories/test.jpg',
        )
        self.product = Product.objects.create(
            product_name='Test product',
            category=self.category,
            price=100,
            product_description='Test product description',
        )

    def test_guest_is_redirected_to_login_from_cart(self):
        response = self.client.get(reverse('cart'))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('cart')}",
            fetch_redirect_response=False,
        )

    def test_add_to_cart_saves_size_and_quantity(self):
        size = SizeVariant.objects.create(size_name='Small', price=10)
        color = ColorVariant.objects.create(color_name='Blue', price=5)
        self.product.size_variant.add(size)
        self.product.color_variant.add(color)
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('add_to_cart', args=[self.product.uid]),
            {
                'quantity': 3,
                'variant': 'Small',
                'color_variant': str(color.uid),
            },
        )

        self.assertRedirects(
            response,
            reverse('get_products', kwargs={'slug': self.product.slug}),
        )
        cart_item = CartItem.objects.get(cart__user=self.user, product=self.product)
        self.assertEqual(cart_item.size_variant, size)
        self.assertEqual(cart_item.color_variant, color)
        self.assertEqual(cart_item.quantity, 3)

    def test_add_to_cart_rejects_get_requests(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse('add_to_cart', args=[self.product.uid]),
        )

        self.assertEqual(response.status_code, 405)
        self.assertFalse(Cart.objects.filter(user=self.user).exists())

    def test_cart_item_cannot_be_removed_by_another_user(self):
        other_user = User.objects.create_user(
            username='other@example.com',
            email='other@example.com',
            password='Secure-test-password-42',
        )
        cart = Cart.objects.create(user=other_user)
        cart_item = CartItem.objects.create(cart=cart, product=self.product)
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('remove_cart', args=[cart_item.uid]),
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(CartItem.objects.filter(uid=cart_item.uid).exists())

    def test_cart_item_quantity_can_be_updated(self):
        cart = Cart.objects.create(user=self.user)
        cart_item = CartItem.objects.create(cart=cart, product=self.product)
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('update_cart_item', args=[cart_item.uid]),
            {'quantity': 5},
        )

        self.assertRedirects(response, reverse('cart'))
        cart_item.refresh_from_db()
        self.assertEqual(cart_item.quantity, 5)

    def test_coupon_cannot_be_removed_from_another_users_cart(self):
        other_user = User.objects.create_user(
            username='other@example.com',
            email='other@example.com',
            password='Secure-test-password-42',
        )
        cart = Cart.objects.create(user=other_user)
        coupon = Coupon.objects.create(
            coupon_code='SAVE20',
            is_expired=False,
            discount_price=20,
            minimum_amount=100,
        )
        cart.coupon = coupon
        cart.save()
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('remove_coupon', args=[cart.uid]),
        )

        self.assertEqual(response.status_code, 404)
        cart.refresh_from_db()
        self.assertEqual(cart.coupon, coupon)

    def test_cart_total_uses_quantity_and_active_coupon(self):
        cart = Cart.objects.create(user=self.user)
        coupon = Coupon.objects.create(
            coupon_code='SAVE20',
            is_expired=False,
            discount_price=20,
            minimum_amount=100,
        )
        cart.coupon = coupon
        cart.save()
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)

        self.assertEqual(cart.get_cart_subtotal(), 200)
        self.assertEqual(cart.get_cart_total(), 180)

    def test_expired_coupon_is_not_applied(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        Coupon.objects.create(
            coupon_code='EXPIRED',
            is_expired=True,
            discount_price=20,
            minimum_amount=100,
        )
        self.client.force_login(self.user)

        response = self.client.post(reverse('cart'), {'coupon': 'EXPIRED'})

        self.assertRedirects(response, reverse('cart'))
        cart.refresh_from_db()
        self.assertIsNone(cart.coupon)

    @override_settings(SITE_URL='https://shop.example')
    def test_activation_email_uses_configured_site_url(self):
        send_account_activation_email('buyer@example.com', 'test-token')

        self.assertIn(
            'https://shop.example/accounts/activate/test-token/',
            mail.outbox[-1].body,
        )

    def test_unknown_product_returns_404(self):
        response = self.client.get(
            reverse('get_products', kwargs={'slug': 'missing-product'}),
        )

        self.assertEqual(response.status_code, 404)

    def test_registration_creates_profile_and_sends_activation_link(self):
        response = self.client.post(
            reverse('register'),
            {
                'first_name': 'New',
                'last_name': 'Customer',
                'email': 'new-customer@example.com',
                'password': 'V3ry-Random!Training-932-Tree',
            },
        )

        self.assertRedirects(response, reverse('register'))
        user = User.objects.get(username='new-customer@example.com')
        self.assertFalse(user.profile.is_email_verified)
        self.assertIn(
            f'/accounts/activate/{user.profile.email_token}/',
            mail.outbox[-1].body,
        )
