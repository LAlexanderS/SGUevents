from typing import Any
from django.contrib import admin
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.contrib.auth import get_user_model

from events_available.models import Events_offline, Events_online, EventOnlineGallery, EventOfflineGallery, MediaFile, EventLogistics

User = get_user_model()

# Проверка группы
def user_in_group(user, group_name):
    return user.groups.filter(name=group_name).exists()

class RestrictedAdminMixin:

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs  # все для суперпольз
        # меропр где польз админ
        return qs.filter(events_admin=request.user)

    def has_change_permission(self, request, obj=None):
        if obj is not None and not request.user.is_superuser:
            # редакт если польз админ
            is_admin = obj.events_admin.filter(pk=request.user.pk).exists()
            return is_admin
        return super().has_change_permission(request, obj)
        

    def has_delete_permission(self, request, obj=None):
        if obj is not None and not request.user.is_superuser:
            # Проверяем, является ли пользователь администратором этого события
            is_admin = obj.events_admin.filter(pk=request.user.pk).exists()
            return is_admin
        return super().has_delete_permission(request, obj)
    
class EventOnlineGalleryInline(admin.TabularInline):
    model = EventOnlineGallery
    extra = 1
    verbose_name = "Фотография"
    verbose_name_plural = "Галерея"
     

@admin.register(Events_online)
class Events_onlineAdmin(RestrictedAdminMixin, admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('secret', 'speakers', 'events_admin', 'member')
    inlines = [EventOnlineGalleryInline]
    list_display = ('name', 'date', 'average_rating_cached')
    readonly_fields = ('average_rating_cached',)

    def get_exclude(self, request, obj = None):
        if request.user.is_superuser:
            return []
        return ['category']
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change and request.user.is_authenticated:
            obj.events_admin.add(request.user)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        if not change and request.user.is_authenticated:
            form.instance.events_admin.add(request.user)


class EventOfflineGalleryInline(admin.TabularInline):
    model = EventOfflineGallery
    extra = 1
    verbose_name = "Фотография"
    verbose_name_plural = "Галерея"


@admin.register(Events_offline)
class Events_offlineAdmin(RestrictedAdminMixin, admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('secret', 'speakers', 'events_admin', 'member')  
    inlines = [EventOfflineGalleryInline]
    list_display = ('name', 'date', 'average_rating_cached')
    readonly_fields = ('average_rating_cached',)
    search_fields = ('name', 'description', 'town')

    def get_exclude(self, request, obj = None):
        if request.user.is_superuser:
            return []
        return ['category']

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change and request.user.is_authenticated:
            obj.events_admin.add(request.user)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        if not change and request.user.is_authenticated:
            form.instance.events_admin.add(request.user)

admin.site.register(MediaFile)

@admin.register(EventLogistics)
class EventLogisticsAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'arrival_datetime', 'departure_datetime', 'transfer_needed')
    list_filter = ('event', 'transfer_needed')
    search_fields = (
        'user__username', 'user__first_name', 'user__last_name',
        'event__name',
        'arrival_flight_number', 'departure_flight_number',
        'hotel_details'
    )
    autocomplete_fields = ['user', 'event']