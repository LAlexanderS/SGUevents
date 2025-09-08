from django import forms
from django.contrib.auth.password_validation import validate_password
from .models import User, Department
from events_available.models import Events_offline, EventLogistics
from bookmarks.models import Registered

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


class UserPasswordChangeForm(forms.Form):
    new_password1 = forms.CharField(
        label='Новый пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Введите новый пароль'}),
    )
    new_password2 = forms.CharField(
        label='Повторите пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Повторите новый пароль'}),
    )

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')

        if not password1:
            self.add_error('new_password1', 'Введите новый пароль')
        if not password2:
            self.add_error('new_password2', 'Повторите пароль')

        if password1 and password2 and password1 != password2:
            self.add_error('new_password2', 'Пароли не совпадают')

        # Прогон через валидаторы Django (использует AUTH_PASSWORD_VALIDATORS)
        if password1:
            try:
                validate_password(password1)
            except forms.ValidationError as e:
                for msg in e.messages:
                    self.add_error('new_password1', msg)

        return cleaned_data


class EventLogisticsForm(forms.ModelForm):
    # event показываем как выпадающий список только из «моих» оффлайн‑мероприятий
    event = forms.ModelChoiceField(
        queryset=Events_offline.objects.none(),
        label="Оффлайн‑мероприятие"
    )

    # Явно задаём поля даты/времени с HTML5‑виджетом datetime-local (с выбором времени)
    arrival_datetime = forms.DateTimeField(
        required=False,
        label="Дата и время прибытия",
        widget=forms.DateTimeInput(attrs={
            "type": "datetime-local",
            "step": "60",
            "placeholder": "ГГГГ‑ММ‑ДД ЧЧ:ММ"
        }),
        input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"]
    )
    departure_datetime = forms.DateTimeField(
        required=False,
        label="Дата и время убытия",
        widget=forms.DateTimeInput(attrs={
            "type": "datetime-local",
            "step": "60",
            "placeholder": "ГГГГ‑ММ‑ДД ЧЧ:ММ"
        }),
        input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"]
    )

    class Meta:
        model = EventLogistics
        exclude = ("user",)  # user НЕ в форме — выставим во вьюхе
        widgets = {
            "hotel_details":      forms.Textarea(attrs={"rows": 3}),
            "meeting_person":     forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, user=None, **kwargs):
        """
        user — обязателен, чтобы ограничить список event.
        """
        super().__init__(*args, **kwargs)
        if user is not None:
            offline_ids = (
                Registered.objects
                .filter(user=user, offline__isnull=False)
                .values_list("offline", flat=True)
            )
            self.fields["event"].queryset = (
                Events_offline.objects.filter(id__in=offline_ids)
                .order_by("-start_datetime")
            )
