from django.contrib import admin
from django.utils.timezone import localtime
from pytz import timezone as pytz_timezone
from bookmarks.models import Favorite, Registered, Review

admin.site.register(Favorite)
admin.site.register(Registered)

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('formatted_date_submitted', 'user', 'event', 'comment')

    def get_exclude(self, request, obj = None):
        if request.user.is_superuser:
            return []
        return ['content_type', 'object_id']
    
    def get_readonly_fields(self, request, obj = None):
        if request.user.is_superuser:
            return []
        return ['user', 'comment']

    def formatted_date_submitted(self, obj):
        local_time = localtime(obj.date_submitted, pytz_timezone('Asia/Novosibirsk'))
        return local_time.strftime('%d.%m.%Y %H:%M')


    formatted_date_submitted.short_description = 'Дата отправки'
    
admin.site.register(Review, ReviewAdmin)


