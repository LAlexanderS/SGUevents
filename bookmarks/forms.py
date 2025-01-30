from django import forms
from events_available.models import Events_online, Events_offline
from events_cultural.models import Attractions, Events_for_visiting
from django.contrib.auth import get_user_model
from bookmarks.models import Registered
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class SendMessageForm(forms.Form):
    event_choices = [
        ('online', 'Онлайн мероприятия'),
        ('offline', 'Оффлайн мероприятия'),
        ('attractions', 'Достопримечательности'),
        ('for_visiting', 'Доступные для посещения'),
    ]

    event_type = forms.ChoiceField(choices=event_choices, label='Тип мероприятия')
    event = forms.ModelChoiceField(queryset=Events_online.objects.none(), label='Мероприятие', required=False)
    message = forms.CharField(widget=forms.Textarea, label='Сообщение')
    send_to_all = forms.BooleanField(label='Отправить всем участникам', required=False, initial=True)
    selected_users = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        label='Выбрать конкретных участников',
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, user=None, **kwargs):
        event_type = kwargs.pop('event_type', None)
        super(SendMessageForm, self).__init__(*args, **kwargs)
        self.user = user

        logger.info(f"Инициализация формы: event_type={event_type}, user={user}")

        # Если тип мероприятия не указан, используем 'online' по умолчанию
        if not event_type:
            event_type = 'online'
        
        self.set_event_queryset(event_type)
        
        # Если пользователь не суперпользователь, показываем только его мероприятия
        if user and not user.is_superuser:
            self.fields['event'].queryset = self.fields['event'].queryset.filter(author=user)

        # Устанавливаем начальное значение для event_type
        self.fields['event_type'].initial = event_type

        # Получаем event_id из POST данных, если они есть
        if args and args[0]:
            event_id = args[0].get('event')
            if event_id:
                try:
                    # Получаем список пользователей для выбранного мероприятия
                    filter_kwargs = {f"{event_type}": event_id}
                    registered_users = Registered.objects.filter(**filter_kwargs)
                    users = User.objects.filter(id__in=registered_users.values_list('user_id', flat=True))
                    self.fields['selected_users'].queryset = users
                    logger.info(f"Обновлен список пользователей для выбора: {[user.username for user in users]}")
                except Exception as e:
                    logger.error(f"Ошибка при получении списка пользователей: {e}")

    def set_event_queryset(self, event_type):
        model_map = {
            'online': Events_online,
            'offline': Events_offline,
            'attractions': Attractions,
            'for_visiting': Events_for_visiting
        }
        
        model = model_map.get(event_type)
        if model:
            logger.info(f"Установка queryset для типа {event_type}")
            if self.user and not self.user.is_superuser:
                self.fields['event'].queryset = model.objects.filter(author=self.user)
            else:
                self.fields['event'].queryset = model.objects.all()
            logger.info(f"Количество мероприятий в queryset: {self.fields['event'].queryset.count()}")
        else:
            logger.warning(f"Неизвестный тип мероприятия: {event_type}")
            self.fields['event'].queryset = Events_online.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        send_to_all = cleaned_data.get('send_to_all')
        selected_users = cleaned_data.get('selected_users')
        event = cleaned_data.get('event')
        event_type = cleaned_data.get('event_type')
        
        logger.info(f"Очистка данных формы: send_to_all={send_to_all}, selected_users={selected_users}, event={event}")
        
        if not send_to_all and not selected_users:
            raise forms.ValidationError("Выберите получателей сообщения или отметьте 'Отправить всем участникам'")
        
        if not event:
            raise forms.ValidationError("Выберите мероприятие")

        # Обновляем queryset для selected_users
        if event:
            filter_kwargs = {f"{event_type}": event}
            registered_users = Registered.objects.filter(**filter_kwargs)
            users = User.objects.filter(id__in=registered_users.values_list('user_id', flat=True))
            self.fields['selected_users'].queryset = users
            logger.info(f"Обновлен список пользователей для выбора при валидации: {[user.username for user in users]}")
        
        return cleaned_data
