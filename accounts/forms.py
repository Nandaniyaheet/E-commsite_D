from django import forms


class CartQuantityForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, max_value=99)


class AddToCartForm(CartQuantityForm):
    variant = forms.CharField(required=False)
    color_variant = forms.UUIDField(required=False)
