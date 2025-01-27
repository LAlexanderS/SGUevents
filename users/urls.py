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
    re_path(r'^auth/telegram/(?P<token>[0-9a-f-]+)/?$', views.telegram_auth, name='telegram_auth'),
    path('telegram-auth/', views.telegram_login_callback, name='telegram_login_callback'),
]
