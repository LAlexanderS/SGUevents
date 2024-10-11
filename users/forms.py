from django import forms
from .models import User, Department

class RegistrationForm(forms.ModelForm):
    department_id = forms.CharField(
        max_length=50,
        required=True,
        label='ID отдела',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Как-в-справочнике'})
    )

    class Meta:
        model = User
        fields = ['last_name', 'first_name', 'middle_name', 'department_id', 'telegram_id']
        widgets = {
            'middle_name': forms.TextInput(attrs={'placeholder': 'Отчество (необязательно)', 'class': 'form-control'}),
            'telegram_id': forms.HiddenInput(),  # Скрытое поле для telegram_id
        }
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'middle_name': 'Отчество',
        }

    def clean_telegram_id(self):
        telegram_id = self.cleaned_data.get('telegram_id')
        if not telegram_id:
            raise forms.ValidationError("Требуется идентификатор Telegram для регистрации.")
        return telegram_id

    def clean_department_id(self):
        department_id = self.cleaned_data.get('department_id')
        if not Department.objects.filter(department_id=department_id).exists():
            raise forms.ValidationError("Отдел с указанным ID не найден.")
        return department_id
