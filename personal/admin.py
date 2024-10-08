from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import GroupAdmin
from django import forms
from users.models import User

# class GroupAdminForm(forms.ModelForm):
#     users = forms.ModelMultipleChoiceField(
#         queryset=User.objects.all(),
#         widget=admin.widgets.FilteredSelectMultiple('Пользователи', is_stacked=False),
#         required=False
#     )

#     class Meta:
#         model = Group
#         fields = '__all__'

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         if self.instance.pk:
#             self.fields['users'].initial = self.instance.user_set.all()

#     def save(self, commit=True):
#         group = super().save(commit=False)
#         if commit:
#             group.save()
#         if group.pk:
#             group.user_set.set(self.cleaned_data['users'])
#             self.save_m2m()
#         return group

# class CustomGroupAdmin(GroupAdmin):
#     form = GroupAdminForm
#     list_display = ('name',)

# admin.site.unregister(Group)
# admin.site.register(Group, CustomGroupAdmin)

