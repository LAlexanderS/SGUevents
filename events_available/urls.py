from django.urls import path, include
from events_available import views

app_name = 'events_available'

urlpatterns = [
    path('', views.index, name='index'),
]