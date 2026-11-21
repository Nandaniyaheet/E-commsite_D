from django.test import TestCase
from django.urls import reverse


class CartAuthenticationTests(TestCase):
    def test_guest_is_redirected_to_login_from_cart(self):
        response = self.client.get(reverse('cart'))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('cart')}",
            fetch_redirect_response=False,
        )
