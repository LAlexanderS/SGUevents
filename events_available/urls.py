from django.urls import path, include
from events_available import views

app_name = 'events_available'

urlpatterns = [
	path('search/online/', views.online, name='search_online'),
	path('search/offline/', views.offline, name='search_offline'),

	path('online/<int:page>/', views.online, name='online'),
	path('online/', views.online, name='online'),
	path('online/<slug:event_slug>/', views.online_card, name='online_card'),
	
	path('offline/<int:page>/', views.online, name='offline'),
	path('offline/', views.offline, name='offline'),
	path('offline/<slug:event_slug>/', views.offline_card, name='offline_card'),
	
	path('submit_review/<int:event_id>/', views.submit_review, name='submit_review'),
	path('autocomplete/places/', views.autocomplete_places, name='autocomplete_places'),
    
	path('autocomplete/event-name/', views.autocomplete_event_name, name='autocomplete_event_name'),

]