from typing import Any
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from datetime import timedelta 
import logging
from django.utils.safestring import mark_safe
from django.conf import settings

from events_available.models import Events_offline, Events_online, EventOnlineGallery, EventOfflineGallery, MediaFile, EventLogistics, EventOfflineCheckList, DefaultTasks

User = get_user_model()
logger = logging.getLogger(__name__)

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

class EventLogisticsRestrictedMixin:
    """
    Миксин для ограничения доступа к логистике событий.
    Администраторы событий видят только логистику своих событий.
    """
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs  # суперпользователь видит все
        # фильтруем по событиям, где пользователь является администратором и актуальные записи + 7 дней 
        seven_days = now() - timedelta(days=7)

        return qs.filter(
            event__events_admin=request.user,
            departure_datetime__gt=seven_days
            )

    def has_change_permission(self, request, obj=None):
        if obj is not None and not request.user.is_superuser:
            # проверяем, является ли пользователь администратором события
            is_admin = obj.event.events_admin.filter(pk=request.user.pk).exists()
            return is_admin
        return super().has_change_permission(request, obj)
        
    def has_delete_permission(self, request, obj=None):
        if obj is not None and not request.user.is_superuser:
            # проверяем, является ли пользователь администратором события
            is_admin = obj.event.events_admin.filter(pk=request.user.pk).exists()
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
    filter_horizontal = [
        'speakers', 'member', 'events_admin', 'secret', 
        'related_online_events', 'related_offline_events',
        'related_attractions', 'related_events_for_visiting'
    ]
    inlines = [EventOnlineGalleryInline]
    list_display = ('name', 'date', 'average_rating_cached')
    readonly_fields = ('average_rating_cached',)

    def gallery_usage_info(self, obj):
        total_bytes = 0
        try:
            if obj:
                for item in obj.gallery.all():
                    if getattr(item, 'image', None) and getattr(item.image, 'name', None):
                        try:
                            total_bytes += item.image.size
                        except Exception:
                            pass
                # include single-file fields if present
                for f in ('qr', 'image', 'documents'):
                    try:
                        file_field = getattr(obj, f, None)
                        if file_field and getattr(file_field, 'name', None):
                            total_bytes += file_field.size
                    except Exception:
                        pass
        except Exception:
            total_bytes = 0
        max_bytes = getattr(settings, 'MAX_GALLERY_UPLOAD_BYTES', 8 * 1024 * 1024)
        used_mb = round(total_bytes / (1024 * 1024), 2)
        max_mb = getattr(settings, 'MAX_GALLERY_UPLOAD_MB', 8)
        # Build JSON with per-file sizes for client-side recalculation on deletes/replaces
        import json
        gallery_items = []
        try:
            if obj:
                for item in obj.gallery.all():
                    try:
                        url = item.image.url if getattr(item, 'image', None) and getattr(item.image, 'url', None) else ''
                    except Exception:
                        url = ''
                    size = 0
                    name = ''
                    try:
                        size = item.image.size
                        name = getattr(item.image, 'name', '')
                    except Exception:
                        pass
                    gallery_items.append({"url": url, "name": name, "size": size})
        except Exception:
            pass
        singles = {}
        for f in ('qr', 'image', 'documents'):
            size_f = 0
            name_f = ''
            try:
                file_field = getattr(obj, f, None)
                if file_field and getattr(file_field, 'name', None):
                    size_f = file_field.size
                    name_f = file_field.name
            except Exception:
                pass
            singles[f] = {"name": name_f, "size": size_f}
        sizes_json = json.dumps({"gallery": gallery_items, "singles": singles})
        html = f'<div id="gallery-usage" data-used-bytes="{total_bytes}" data-max-bytes="{max_bytes}">Использовано {used_mb} МБ из {max_mb} МБ</div><script type="application/json" id="gallery-sizes">{sizes_json}</script>'
        return mark_safe(html)
    gallery_usage_info.short_description = "Размер изображений"

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if 'gallery_usage_info' not in fields:
            return ['gallery_usage_info'] + list(fields)
        return fields

    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))
        if 'gallery_usage_info' not in ro:
            ro.append('gallery_usage_info')
        return ro

    class Media:
        js = ('js/admin/gallery_quota.js',)

    def get_exclude(self, request, obj = None):
        if request.user.is_superuser:
            return []
        return ['category']
    
    def save_model(self, request, obj, form, change):
        # Server-side quota validation: existing bytes + all uploaded files in this request
        existing_bytes = 0
        try:
            # existing gallery images
            if change and obj.pk:
                db_obj = Events_online.objects.get(pk=obj.pk)
                for item in db_obj.gallery.all():
                    if getattr(item, 'image', None) and getattr(item.image, 'name', None):
                        try:
                            existing_bytes += item.image.size
                        except Exception:
                            pass
                # include single-file fields if present on saved object
                for f in ('qr', 'image', 'documents'):
                    try:
                        file_field = getattr(db_obj, f, None)
                        if file_field and getattr(file_field, 'name', None):
                            existing_bytes += file_field.size
                    except Exception:
                        pass
        except Exception:
            existing_bytes = 0

        uploaded_bytes = 0
        try:
            for f in request.FILES.values():
                try:
                    uploaded_bytes += getattr(f, 'size', 0) or 0
                except Exception:
                    pass
        except Exception:
            uploaded_bytes = 0

        max_bytes = getattr(settings, 'MAX_GALLERY_UPLOAD_BYTES', 8 * 1024 * 1024)
        if existing_bytes + uploaded_bytes > max_bytes:
            raise ValidationError('Превышен размер загружаемых файлов')

        super().save_model(request, obj, form, change)
        if not change and request.user.is_authenticated:
            obj.events_admin.add(request.user)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        if not change and request.user.is_authenticated:
            form.instance.events_admin.add(request.user)

@admin.register(DefaultTasks)
class DefaultTasksAdmin(admin.ModelAdmin):
    search_fields = ['name']

class EventOfflineCheckListInline(admin.TabularInline):
    model = EventOfflineCheckList
    extra = 0
    autocomplete_fields = ['task_name','responsible']

class EventOfflineGalleryInline(admin.TabularInline):
    model = EventOfflineGallery
    extra = 1
    verbose_name = "Фотография"
    verbose_name_plural = "Галерея"


@admin.register(Events_offline)
class Events_offlineAdmin(RestrictedAdminMixin, admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = [
        'speakers', 'member', 'events_admin', 'secret', 
        'related_online_events', 'related_offline_events',
        'related_attractions', 'related_events_for_visiting'
    ]  
    inlines = [EventOfflineGalleryInline, EventOfflineCheckListInline]
    list_display = ('name', 'date', 'average_rating_cached')
    readonly_fields = ('average_rating_cached', 'date_add')
    search_fields = ('name', 'description', 'town')

    def gallery_usage_info(self, obj):
        total_bytes = 0
        try:
            if obj:
                for item in obj.gallery.all():
                    if getattr(item, 'image', None) and getattr(item.image, 'name', None):
                        try:
                            total_bytes += item.image.size
                        except Exception:
                            pass
                for f in ('qr', 'image', 'documents'):
                    try:
                        file_field = getattr(obj, f, None)
                        if file_field and getattr(file_field, 'name', None):
                            total_bytes += file_field.size
                    except Exception:
                        pass
        except Exception:
            total_bytes = 0
        max_bytes = getattr(settings, 'MAX_GALLERY_UPLOAD_BYTES', 8 * 1024 * 1024)
        used_mb = round(total_bytes / (1024 * 1024), 2)
        max_mb = getattr(settings, 'MAX_GALLERY_UPLOAD_MB', 8)
        import json
        gallery_items = []
        try:
            if obj:
                for item in obj.gallery.all():
                    try:
                        url = item.image.url if getattr(item, 'image', None) and getattr(item.image, 'url', None) else ''
                    except Exception:
                        url = ''
                    size = 0
                    name = ''
                    try:
                        size = item.image.size
                        name = getattr(item.image, 'name', '')
                    except Exception:
                        pass
                    gallery_items.append({"url": url, "name": name, "size": size})
        except Exception:
            pass
        singles = {}
        for f in ('qr', 'image', 'documents'):
            size_f = 0
            name_f = ''
            try:
                file_field = getattr(obj, f, None)
                if file_field and getattr(file_field, 'name', None):
                    size_f = file_field.size
                    name_f = file_field.name
            except Exception:
                pass
            singles[f] = {"name": name_f, "size": size_f}
        sizes_json = json.dumps({"gallery": gallery_items, "singles": singles})
        html = f'<div id="gallery-usage" data-used-bytes="{total_bytes}" data-max-bytes="{max_bytes}">Использовано {used_mb} МБ из {max_mb} МБ</div><script type="application/json" id="gallery-sizes">{sizes_json}</script>'
        return mark_safe(html)
    gallery_usage_info.short_description = "Размер изображений"

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if 'gallery_usage_info' not in fields:
            return ['gallery_usage_info'] + list(fields)
        return fields

    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))
        if 'gallery_usage_info' not in ro:
            ro.append('gallery_usage_info')
        return ro

    class Media:
        js = ('js/admin/gallery_quota.js',)

    def get_exclude(self, request, obj = None):
        if request.user.is_superuser:
            return []
        return ['category', 'save_media_to_disk', 'yandex_disk_link']

    def save_model(self, request, obj, form, change):
        # Server-side quota validation: existing bytes + all uploaded files in this request
        existing_bytes = 0
        try:
            if change and obj.pk:
                db_obj = Events_offline.objects.get(pk=obj.pk)
                for item in db_obj.gallery.all():
                    if getattr(item, 'image', None) and getattr(item.image, 'name', None):
                        try:
                            existing_bytes += item.image.size
                        except Exception:
                            pass
                for f in ('qr', 'image', 'documents'):
                    try:
                        file_field = getattr(db_obj, f, None)
                        if file_field and getattr(file_field, 'name', None):
                            existing_bytes += file_field.size
                    except Exception:
                        pass
        except Exception:
            existing_bytes = 0

        uploaded_bytes = 0
        try:
            for f in request.FILES.values():
                try:
                    uploaded_bytes += getattr(f, 'size', 0) or 0
                except Exception:
                    pass
        except Exception:
            uploaded_bytes = 0

        max_bytes = getattr(settings, 'MAX_GALLERY_UPLOAD_BYTES', 8 * 1024 * 1024)
        if existing_bytes + uploaded_bytes > max_bytes:
            raise ValidationError('Превышен размер загружаемых файлов')

        super().save_model(request, obj, form, change)
        if not change and request.user.is_authenticated:
            obj.events_admin.add(request.user)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        if not change and request.user.is_authenticated:
            form.instance.events_admin.add(request.user)

admin.site.register(MediaFile)


@admin.register(EventLogistics)
class EventLogisticsAdmin(EventLogisticsRestrictedMixin, admin.ModelAdmin):
    list_display = ('user', 'event', 'arrival_datetime', 'departure_datetime', 'transfer_needed', 'meeting_person')
    list_filter = ('event', 'transfer_needed')
    search_fields = (
        'user__username', 'user__first_name', 'user__last_name',
        'event__name',
        'arrival_flight_number', 'departure_flight_number',
        'hotel_details'
    )
    autocomplete_fields = ['user', 'event']

