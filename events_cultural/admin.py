from django.contrib import admin

from events_cultural.models import Attractions, Events_for_visiting
from django.contrib.auth import get_user_model

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

@admin.register(Attractions)
class AttractionsAdmin(RestrictedAdminMixin, admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('secret','events_admin','member')

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

@admin.register(Events_for_visiting)
class Events_for_visitingAdmin(RestrictedAdminMixin, admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('secret','events_admin', 'member')

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



