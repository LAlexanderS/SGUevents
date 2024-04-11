from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static

from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('general/', include('main.urls', namespace='main')),
		path('support/', include('support.urls', namespace='support')),
		path('events_available/', include('events_available.urls', namespace='events_available')),
		path('events_calendar/', include('events_calendar.urls', namespace='events_calendar')),
		path('events_cultural/', include('events_cultural.urls', namespace='events_cultural')),
		path('application_for_admin_rights/', include('application_for_admin_rights.urls', namespace='application_for_admin_rights')),
		path('personal/', include('personal.urls', namespace='personal')),
		path('bookmarks/', include('bookmarks.urls', namespace='bookmarks')),
		path('', include('users.urls', namespace='users')),
]

if settings.DEBUG: 
	urlpatterns += [
		path("__debug__/", include("debug_toolbar.urls")),
    ]
	urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)