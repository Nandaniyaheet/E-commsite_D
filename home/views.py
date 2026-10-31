from django.shortcuts import render
from product.models import Product
# Create your views here.
def index(request):
    context = {'products' : Product.objects.all()}
    return render(request , 'home/index.html' , context)



def search(request):
    query = request.GET.get('query')
    products = []

    if query:
        products = Product.objects.filter(product_name__icontains=query)

    context = {
        'products': products,
        'query': query,
    }
    return render(request, 'home/search_results.html', context)

