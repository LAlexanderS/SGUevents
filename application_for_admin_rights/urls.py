from django.urls import path, include
from application_for_admin_rights import views

app_name = 'application_for_admin_rights'

urlpatterns = [
    path('', views.index, name='index'),
]