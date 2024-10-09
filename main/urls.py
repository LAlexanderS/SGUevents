from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.index, name='index'),
	path('search/all/', views.index, name='search_all'),
    path('autocomplete/event-name/', views.autocomplete_event_name, name='autocomplete_event_name')
]
