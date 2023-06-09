# chatterbox_app/urls.py
from django.urls import path
from . import views
from allauth.account.views import LoginView, LogoutView, PasswordChangeView


app_name = 'chatterbox_app'

urlpatterns = [
    path('', views.home, name='home'),
    path('my_account/', views.my_account, name='my_account'),
]