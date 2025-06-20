from accounts.views import login_page
from django.urls import path


urlpatterns = {
    path('login/', login_page, name="login"),
}
