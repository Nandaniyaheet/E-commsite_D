#from accounts.views import login_page, register_page, activate_email
from django.urls import path
from . import views

urlpatterns = [
   path('login/' , views.login_page , name="login" ),
   path('register/' , views.register_page , name="register"),
   path('activate/<str:email_token>/' , views.activate_email , name="activate_email"),
]
