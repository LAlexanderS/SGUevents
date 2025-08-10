from django.urls import path, re_path
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('change_password/', views.change_password, name='change_password'),
    path('request_admin_rights/', views.request_admin_rights, name='request_admin_rights'),
    path('event_support_request/', views.event_support_request, name='event_support_request'),
    path('upload-photo/', views.upload_photo, name='upload_photo'),
    path('delete-photo/', views.delete_photo, name='delete_photo'),
    path('fetch-telegram-photo/', views.fetch_telegram_photo, name='fetch_telegram_photo'),
    re_path(r'^auth/telegram/(?P<token>[0-9a-f-]+)/?$', views.telegram_auth, name='telegram_auth'),
    path('telegram-auth/', views.telegram_login_callback, name='telegram_login_callback'),
]
