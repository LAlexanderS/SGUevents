from django import forms
from events_available.models import Events_online, Events_offline
from events_cultural.models import Attractions, Events_for_visiting
from django.contrib.auth import get_user_model
from bookmarks.models import Registered

User = get_user_model()

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

        # Если тип мероприятия не указан, определяем лучший по умолчанию для пользователя
        if not event_type:
            if user and not user.is_superuser:
                # Для обычных админов - ищем тип где есть мероприятия
                from events_available.models import Events_online, Events_offline
                from events_cultural.models import Attractions, Events_for_visiting
                
                if Events_offline.objects.filter(events_admin=user).exists():
                    event_type = 'offline'
                elif Events_online.objects.filter(events_admin=user).exists():
                    event_type = 'online'
                elif Attractions.objects.filter(events_admin=user).exists():
                    event_type = 'attractions'
                elif Events_for_visiting.objects.filter(events_admin=user).exists():
                    event_type = 'for_visiting'
                else:
                    event_type = 'online'  # По умолчанию если нет мероприятий
            else:
                event_type = 'online'  # Для суперпользователей - онлайн
        
        self.set_event_queryset(event_type)
        
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
                except Exception as e:
                    pass

    def set_event_queryset(self, event_type):
        model_map = {
            'online': Events_online,
            'offline': Events_offline,
            'attractions': Attractions,
            'for_visiting': Events_for_visiting
        }
        
        model = model_map.get(event_type)
        if model:
            if self.user and not self.user.is_superuser:
                self.fields['event'].queryset = model.objects.filter(events_admin=self.user)
            else:
                self.fields['event'].queryset = model.objects.all()
        else:
            self.fields['event'].queryset = Events_online.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        send_to_all = cleaned_data.get('send_to_all')
        selected_users = cleaned_data.get('selected_users')
        event = cleaned_data.get('event')
        event_type = cleaned_data.get('event_type')
        
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
        
        return cleaned_data
