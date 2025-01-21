from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Department, AdminRightRequest, SupportRequest


class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('department_id', 'department_name')
    search_fields = ('department_id', 'department_name')

class UserAdmin(BaseUserAdmin):
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
