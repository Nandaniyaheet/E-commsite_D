from django.shortcuts import get_object_or_404, render
from product.models import Product


def get_products(request, slug):
    product = get_object_or_404(
        Product.objects.prefetch_related(
            'size_variant',
            'color_variant',
            'product_images',
        ),
        slug=slug,
    )
    context = {'product': product}
    size = request.GET.get('size')
    if size:
        size_variant = get_object_or_404(product.size_variant, size_name=size)
        context['selected_size'] = size
        context['updated_price'] = product.price + size_variant.price
    return render(request, 'product/product.html', context)