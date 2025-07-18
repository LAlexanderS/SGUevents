from django.contrib import admin
from django.urls import path, include, re_path
from django.conf.urls.static import static
from django.conf import settings
from django.views.static import serve
from users.views import telegram_webhook
from django.conf.urls import handler404, handler500, handler403, handler400

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls', namespace='users')),
    path('support/', include('support.urls', namespace='support')),
    path('events_available/', include('events_available.urls', namespace='events_available')),
    path('events_calendar/', include('events_calendar.urls', namespace='events_calendar')),
    path('events_cultural/', include('events_cultural.urls', namespace='events_cultural')),
    path('application_for_admin_rights/', include('application_for_admin_rights.urls', namespace='application_for_admin_rights')),
    path('personal/', include('personal.urls', namespace='personal')),
    path('select2/', include('django_select2.urls')),
    path('bookmarks/', include('bookmarks.urls', namespace='bookmarks')),
    path('webhook/', telegram_webhook, name='telegram_webhook'),
    path('', include('main.urls', namespace='main')),
]

if settings.DEBUG:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]

# Обслуживание статических и медиа файлов (для локальной разработки и не-nginx окружений)
# Принудительное обслуживание статики даже при DEBUG=False
urlpatterns += [
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

handler404 = 'main.views.custom_404'
handler500 = 'main.views.custom_500'
handler403 = 'main.views.custom_403'
handler400 = 'main.views.custom_400'
