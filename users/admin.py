from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Department, AdminRightRequest, SupportRequest

# Переопределяем права доступа к модулю users для staff
original_has_module_permission = admin.site.has_permission

def custom_has_permission(request):
    """Разрешаем staff доступ к админке"""
    return request.user.is_active and (request.user.is_staff or request.user.is_superuser)

admin.site.has_permission = custom_has_permission

class StaffReadOnlyMixin:
    """Миксин для предоставления staff только прав на просмотр"""
    
    def has_view_permission(self, request, obj=None):
        """Staff могут просматривать"""
        return request.user.is_staff or request.user.is_superuser
    
    def has_module_permission(self, request):
        """Staff видят модуль в админке"""
        return request.user.is_staff or request.user.is_superuser
    
    def has_add_permission(self, request):
        """Только суперюзеры могут добавлять"""
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        """Только суперюзеры могут изменять"""
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        """Только суперюзеры могут удалять"""
        return request.user.is_superuser

class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('department_id', 'department_name')
    search_fields = ('department_id', 'department_name')

class UserAdmin(StaffReadOnlyMixin, BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'middle_name', 'email', 'department')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Additional info'), {'fields': ('telegram_id', 'vip')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'middle_name', 'email', 'department')}),
        (_('Additional info'), {'fields': ('telegram_id', 'vip')}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'middle_name', 'department', 'telegram_id', 'is_staff')
    search_fields = ('username', 'first_name', 'last_name', 'middle_name', 'email', 'department__department_id', 'telegram_id')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'department')

    def get_model_perms(self, request):
        """
        Переопределяем проверку прав для отображения модели в админке.
        Staff пользователи должны видеть модель User.
        """
        perms = super().get_model_perms(request)
        if request.user.is_staff:
            # Принудительно добавляем права для staff
            perms['view'] = True
        return perms

class AdminRightRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'reason', 'status', 'response')
    list_filter = ('status',)
    search_fields = ('user__username', 'user__email', 'reason', 'response')
    raw_id_fields = ('user',)  # Это позволяет более удобно работать с ForeignKey полями

class SupportRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'answer', 'created_at', 'is_resolved')
    list_filter = ('is_resolved', 'created_at')
    search_fields = ('user__username', 'user__email', 'question', 'answer')
    raw_id_fields = ('user',)

admin.site.register(User, UserAdmin)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(AdminRightRequest, AdminRightRequestAdmin)
admin.site.register(SupportRequest, SupportRequestAdmin)
