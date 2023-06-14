# chatterbox_app/urls.py
from django.urls import path
from . import views
from allauth.account.views import LoginView, LogoutView, PasswordChangeView, ConfirmEmailView

app_name = 'chatterbox_app'

urlpatterns = [
    path('', views.home, name='home'),
    path('my_account/', views.my_account, name='my_account'),
    path('contacts/', views.contact_list, name='contact_list'),
    path('contact/new/', views.contact_create, name='contact_create'),
    path('contact/<int:pk>/delete/', views.contact_delete, name='contact_delete'),
    path('contact/<int:pk>/edit/', views.contact_update, name='contact_update'),
    path('email/inbox/', views.email_inbox, name='email_inbox'),
    path('contact/<int:contact_id>/email/', views.send_email, name='send_email'),
    path('contact/<int:pk>/', views.ContactDetailView.as_view(), name='contact_detail'),
    path('contact/<int:pk>/add_note/', views.add_note, name='add_note'),
    path('contact/<int:contact_pk>/note/<int:pk>/edit/', views.note_edit, name='note_edit'),
    path('contact/<int:contact_pk>/note/<int:pk>/delete/', views.note_delete, name='note_delete'),
]
