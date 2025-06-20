from django.shortcuts import render

# Create your views here.
def login_page(request):
    return render(request, 'accounts/login.html')



#http://127.0.0.1:8000/accounts/login/?#