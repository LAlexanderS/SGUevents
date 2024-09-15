from django.urls import path, include
from events_cultural import views

app_name = 'events_cultural'

urlpatterns = [
	path('attractions/search/', views.attractions, name='search_attractions'),
	path('events_for_visiting/search/', views.events_for_visiting, name='search_events_for_visiting'),


	path('attractions/<int:page>/', views.attractions, name='attractions'),
	path('attractions/', views.attractions, name='attractions'),
	path('attractions/<slug:event_slug>/', views.attractions_card, name='attractions_card'),

	# path('events_registered/', views.events_registered, name='events_registered'),
	# path('events_registered/<int:event_id>', views.events_registered_, name='events_registered_card'),
	# path('events_registered/event/<slug:event_slug>/', views.events_registered, name='events_registered_card'),

	path('events_for_visiting/<int:page>/', views.events_for_visiting, name='events_for_visiting'),
	path('events_for_visiting/', views.events_for_visiting, name='events_for_visiting'),
	path('events_for_visiting/<slug:event_slug>/', views.for_visiting_card, name='events_for_visiting_card'),

	path('submit_review/<int:event_id>/', views.submit_review, name='submit_review'),
 
 path('autocomplete/event-name/', views.autocomplete_event_name, name='autocomplete_event_name'),

]