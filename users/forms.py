from django import forms
from .models import User, Department

class RegistrationForm(forms.ModelForm):
    department_id = forms.CharField(
        max_length=50,
        required=True,
        label='ID отдела',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Как-в-справочнике'})
    )

    # Флаг "отчество отсутствует" — управляет обязательностью поля middle_name
    no_middle_name = forms.BooleanField(
        required=False,
        label='Отчество отсутствует',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_no_middle_name'})
    )

    class Meta:
        model = User
        fields = ['last_name', 'first_name', 'middle_name', 'department_id', 'telegram_id']
        widgets = {
            'middle_name': forms.TextInput(attrs={'placeholder': 'Отчество', 'class': 'form-control'}),
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

    def clean(self):
        cleaned = super().clean()
        first_name = (cleaned.get('first_name') or '').strip()
        last_name = (cleaned.get('last_name') or '').strip()
        middle_name = (cleaned.get('middle_name') or '')
        no_middle = bool(cleaned.get('no_middle_name'))

        # Фамилия и имя всегда обязательны
        if not last_name:
            self.add_error('last_name', 'Укажите фамилию')
        if not first_name:
            self.add_error('first_name', 'Укажите имя')

        # Если галочка НЕ стоит — отчество обязательно
        if not no_middle:
            if not (middle_name or '').strip():
                self.add_error('middle_name', 'Укажите отчество или отметьте «Отчество отсутствует»')
        else:
            # Если отмечено отсутствие отчества — сохраняем пустым
            cleaned['middle_name'] = ''

        return cleaned
