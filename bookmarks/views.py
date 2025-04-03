from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from bookmarks.models import Favorite, Registered, Review
from events_available.models import Events_online, Events_offline
from events_cultural.models import Attractions, Events_for_visiting
from users.telegram_utils import send_message_to_user
from events_cultural.views import submit_review
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from bookmarks.forms import SendMessageForm
from users.telegram_utils import send_notification_with_toggle
from bookmarks.models import Registered
from django.utils.timezone import now
import logging

logger = logging.getLogger(__name__)


@login_required
def events_add(request, event_slug):
    event = None
    event_type = None
    try:
        event = Events_online.objects.get(slug=event_slug)
        event_type = 'online'
    except Events_online.DoesNotExist:
        try:
            event = Events_offline.objects.get(slug=event_slug)
            event_type = 'offline'
        except Events_offline.DoesNotExist:
            try:
                event = Attractions.objects.get(slug=event_slug)
                event_type = 'attractions'
            except Attractions.DoesNotExist:
                try:
                    event = Events_for_visiting.objects.get(slug=event_slug)
                    event_type = 'for_visiting'
                except Events_for_visiting.DoesNotExist:
                    pass

    if event and request.user.is_authenticated:
        favorite, created = None, False
        if event_type == 'online':
            favorite, created = Favorite.objects.get_or_create(user=request.user, online=event)
        elif event_type == 'offline':
            favorite, created = Favorite.objects.get_or_create(user=request.user, offline=event)
        elif event_type == 'attractions':
            favorite, created = Favorite.objects.get_or_create(user=request.user, attractions=event)
        elif event_type == 'for_visiting':
            favorite, created = Favorite.objects.get_or_create(user=request.user, for_visiting=event)

        if not created:
            favorite.delete()
            added = False
        else:
            added = True

        return JsonResponse({'added': added, 'event_id': favorite.id})

    return JsonResponse({'error': 'Event not found or user not authenticated'}, status=400)

@login_required
def events_remove(request, event_id):
    if request.method == 'POST':
        favorite = get_object_or_404(Favorite, id=event_id, user=request.user)
        favorite.delete()
        return JsonResponse({'removed': True})
    return JsonResponse({'removed': False, 'error': 'Invalid request method'}, status=400)

@login_required
def favorites(request):
    favorites = Favorite.objects.filter(user=request.user).order_by('-created_timestamp')

    events = []
    for fav in favorites:
        if fav.online:
            events.append(fav.online)
        elif fav.offline:
            events.append(fav.offline)
        elif fav.attractions:
            events.append(fav.attractions)
        elif fav.for_visiting:
            events.append(fav.for_visiting)

    reviews = {}
    for event in events:
        content_type = ContentType.objects.get_for_model(event)
        reviews[event.unique_id] = Review.objects.filter(content_type=content_type, object_id=event.id)

    registered_dict = {
        'online': {},
        'offline': {},
        'attractions': {},
        'for_visiting': {}
    }

    # Получаем все зарегистрированные мероприятия и распределяем их по типам
    for event in events:
        if isinstance(event, Events_online):
            reg_event = Registered.objects.filter(user=request.user, online=event).first()
            if reg_event:
                registered_dict['online'][event.id] = reg_event.id
        elif isinstance(event, Events_offline):
            reg_event = Registered.objects.filter(user=request.user, offline=event).first()
            if reg_event:
                registered_dict['offline'][event.id] = reg_event.id
        elif isinstance(event, Attractions):
            reg_event = Registered.objects.filter(user=request.user, attractions=event).first()
            if reg_event:
                registered_dict['attractions'][event.id] = reg_event.id
        elif isinstance(event, Events_for_visiting):
            reg_event = Registered.objects.filter(user=request.user, for_visiting=event).first()
            if reg_event:
                registered_dict['for_visiting'][event.id] = reg_event.id

    registered_flat = {}
    for subdict in registered_dict.values():
        registered_flat.update(subdict)

    context = {
        'events': events,
        'reviews': reviews,
        'favorites': favorites,
        'registered': registered_flat,
        'now': now().date(),
        'name_page': 'Избранные',
    }
    return render(request, 'bookmarks/favorites.html', context)

def events_attended(request):
    pass
    return render(request, "bookmarks/events_attended.html")

@login_required
def events_registered(request, event_slug):
    event = None
    event_type = None
    favorites = Favorite.objects.filter(user=request.user)

    try:
        event = Events_online.objects.get(slug=event_slug)
        event_type = 'online'
    except Events_online.DoesNotExist:
        try:
            event = Events_offline.objects.get(slug=event_slug)
            event_type = 'offline'
        except Events_offline.DoesNotExist:
            try:
                event = Attractions.objects.get(slug=event_slug)
                event_type = 'attractions'
            except Attractions.DoesNotExist:
                try:
                    event = Events_for_visiting.objects.get(slug=event_slug)
                    event_type = 'for_visiting'
                except Events_for_visiting.DoesNotExist:
                    pass

    if event and request.user.is_authenticated:
        registered, created = None, False
        if event_type == 'online':
            registered, created = Registered.objects.get_or_create(user=request.user, online=event)
        elif event_type == 'offline':
            registered, created = Registered.objects.get_or_create(user=request.user, offline=event)
        elif event_type == 'attractions':
            registered, created = Registered.objects.get_or_create(user=request.user, attractions=event)
        elif event_type == 'for_visiting':
            registered, created = Registered.objects.get_or_create(user=request.user, for_visiting=event)

        event.member.add(request.user)

        if created:
            response_data = {'added': True, 'event_id': registered.id, 'event_slug': event_slug}
            if event_type == 'for_visiting':
                event.place_free -= 1
                event.save(update_fields=['place_free'])
                response_data['place_free'] = event.place_free
            return JsonResponse(response_data)
        else:
            return JsonResponse({'added': False, 'error': 'Уже зарегистрированы'}, status=400)

    return JsonResponse({'error': 'Event not found or user not authenticated'}, status=400)

@login_required
def registered_remove(request, event_id):
    if request.method == 'POST':
        event = get_object_or_404(Registered, id=event_id, user=request.user)
        event_slug = (
            event.for_visiting.slug if event.for_visiting else (
                event.online.slug if event.online else (
                    event.offline.slug if event.offline else (
                        event.attractions.slug if event.attractions else None
                    )
                )
            )
        )
        event_name = (
            event.for_visiting.name if event.for_visiting else (
                event.online.name if event.online else (
                    event.offline.name if event.offline else (
                        event.attractions.name if event.attractions else None
                    )
                )
            )
        )

        if event.for_visiting:
            event.for_visiting.member.remove(request.user)
            event.for_visiting.place_free += 1
            event.for_visiting.save(update_fields=['place_free'])
        elif event.online:
            event.online.member.remove(request.user)
        elif event.offline:
            event.offline.member.remove(request.user)

        event.delete()
        telegram_id = request.user.telegram_id
        if telegram_id:
            message = f"\U0000274C Вы успешно отменили регистрацию на мероприятие: {event_name}"
            send_message_to_user(telegram_id, message)
        
        response_data = {'removed': True, 'event_slug': event_slug, 'event_name': event_name}
        if event.for_visiting:
            response_data['place_free'] = event.for_visiting.place_free
        return JsonResponse(response_data)

    return JsonResponse({'removed': False, 'error': 'Invalid request method'}, status=400)

@login_required
def registered(request):
    registered = Registered.objects.filter(user=request.user)
    reviews = {}
    events = []

    online_ids = []
    offline_ids = []
    attractions_ids = []
    for_visiting_ids = []

    registered_ids = set()
    registered_event_map = {}

    for reg in registered:
        if reg.online:
            events.append(reg.online)
            online_ids.append(reg.online.id)
            registered_ids.add(reg.online.id)
            registered_event_map[reg.online.id] = reg.id
        elif reg.offline:
            events.append(reg.offline)
            offline_ids.append(reg.offline.id)
            registered_ids.add(reg.offline.id)
            registered_event_map[reg.offline.id] = reg.id
        elif reg.attractions:
            events.append(reg.attractions)
            attractions_ids.append(reg.attractions.id)
            registered_ids.add(reg.attractions.id)
            registered_event_map[reg.attractions.id] = reg.id
        elif reg.for_visiting:
            events.append(reg.for_visiting)
            for_visiting_ids.append(reg.for_visiting.id)
            registered_ids.add(reg.for_visiting.id)
            registered_event_map[reg.for_visiting.id] = reg.id

    for event in events:
        content_type = ContentType.objects.get_for_model(event)
        reviews[event.unique_id] = Review.objects.filter(content_type=content_type, object_id=event.id)

    favorites_online_id = Favorite.objects.filter(user=request.user, online_id__in=online_ids).values_list('online_id', 'id')
    favorites_offline_id = Favorite.objects.filter(user=request.user, offline_id__in=offline_ids).values_list('offline_id', 'id')
    favorites_attractions_id = Favorite.objects.filter(user=request.user, attractions_id__in=attractions_ids).values_list('attractions_id', 'id')
    favorites_for_visiting_id = Favorite.objects.filter(user=request.user, for_visiting_id__in=for_visiting_ids).values_list('for_visiting_id', 'id')

    favorites_dict = {
        'online': {item[0]: item[1] for item in favorites_online_id},
        'offline': {item[0]: item[1] for item in favorites_offline_id},
        'attractions': {item[0]: item[1] for item in favorites_attractions_id},
        'for_visiting': {item[0]: item[1] for item in favorites_for_visiting_id},
    }

    favorites_online = Favorite.objects.filter(user=request.user, online_id__in=online_ids).select_related('online')
    favorites_offline = Favorite.objects.filter(user=request.user, offline_id__in=offline_ids).select_related('offline')
    favorites_attractions = Favorite.objects.filter(user=request.user, attractions_id__in=attractions_ids).select_related('attractions')
    favorites_for_visiting = Favorite.objects.filter(user=request.user, for_visiting_id__in=for_visiting_ids).select_related('for_visiting')

    liked_slugs = [
    favorite.online.slug for favorite in favorites_online if favorite.online
] + [
    favorite.offline.slug for favorite in favorites_offline if favorite.offline
] + [
    favorite.attractions.slug for favorite in favorites_attractions if favorite.attractions
] + [
    favorite.for_visiting.slug for favorite in favorites_for_visiting if favorite.for_visiting
]

    context = {
        'registered': registered,
        'registered_ids': registered_ids, #для кнопки регистрация/отмена
        'registered_map': registered_event_map, #для data-event-id в регистрации
        'reviews': reviews,
        'name_page': 'Зарегистрированные',
        'liked': liked_slugs,
        'favorites': favorites_dict,

    }
    return render(request, 'bookmarks/registered.html', context)


@staff_member_required
def get_event_choices(request):
    event_type = request.GET.get('event_type')
    events = []

    if event_type == 'online':
        events = Events_online.objects.filter(events_admin=request.user)
    elif event_type == 'offline':
        events = Events_offline.objects.filter(events_admin=request.user)
    elif event_type == 'attractions':
        events = Attractions.objects.filter(events_admin=request.user)
    elif event_type == 'for_visiting':
        events = Events_for_visiting.objects.filter(events_admin=request.user)

    event_data = [{'id': event.id, 'name': event.name} for event in events]
    return JsonResponse(event_data, safe=False)

@staff_member_required
def send_message_to_participants(request):
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "У вас нет прав для отправки сообщений.")
        return redirect('home')

    if request.method == 'POST':
        event_type = request.POST.get('event_type')
        logger.info(f"Получены POST-данные: {request.POST}")
        logger.info(f"Выбранный тип мероприятия: {event_type}")
        
        form = SendMessageForm(request.POST, event_type=event_type, user=request.user)
        if form.is_valid():
            logger.info("Форма валидна")
            event = form.cleaned_data['event']
            message = form.cleaned_data['message']
            send_to_all = form.cleaned_data['send_to_all']
            selected_users = form.cleaned_data.get('selected_users', [])

            logger.info(f"Очищенные данные формы: event={event}, send_to_all={send_to_all}, selected_users={[user.username for user in selected_users]}")
            
            if not event:
                messages.error(request, "Пожалуйста, выберите мероприятие.")
                return redirect('bookmarks:send_message_to_participants')

            # Проверяем права доступа к мероприятию
            if not request.user.is_superuser and event.author != request.user:
                messages.error(request, "У вас нет прав для отправки сообщений участникам этого мероприятия.")
                return redirect('bookmarks:send_message_to_participants')

            # Получаем всех зарегистрированных участников для данного мероприятия
            filter_kwargs = {f"{event_type}": event}
            registered_users = Registered.objects.filter(**filter_kwargs)
            
            logger.info(f"Найдено {registered_users.count()} участников для мероприятия {event.name}")

            if not registered_users.exists():
                messages.error(request, "Нет зарегистрированных участников для выбранного мероприятия.")
                return redirect('bookmarks:send_message_to_participants')

            # Отправляем сообщения
            sent_count = 0
            for registration in registered_users:
                should_send = send_to_all or (selected_users and registration.user in selected_users)
                logger.info(f"Проверка отправки для {registration.user.username}: send_to_all={send_to_all}, selected_users_empty={not selected_users}, в selected_users={registration.user in selected_users}, итоговое решение={should_send}")
                
                if should_send:
                    if registration.user.telegram_id:
                        try:
                            logger.info(f"Отправка сообщения пользователю {registration.user.username} (Telegram ID: {registration.user.telegram_id})")
                            response = send_notification_with_toggle(
                                telegram_id=registration.user.telegram_id,
                                message=message,
                                event_id=event.unique_id,
                                notifications_enabled=True
                            )
                            logger.info(f"Ответ от Telegram API: {response}")
                            if response and response.get('ok'):
                                sent_count += 1
                                logger.info(f"Сообщение успешно отправлено пользователю {registration.user.username}")
                            else:
                                logger.error(f"Ошибка отправки сообщения пользователю {registration.user.username}: {response.get('description', 'Неизвестная ошибка')}")
                        except Exception as e:
                            logger.error(f"Ошибка отправки сообщения пользователю {registration.user.username}: {e}")
                    else:
                        logger.warning(f"У пользователя {registration.user.username} нет Telegram ID")

            if sent_count > 0:
                messages.success(request, f"Сообщения успешно отправлены {sent_count} участникам.")
            else:
                messages.warning(request, "Не удалось отправить ни одного сообщения.")
            return redirect('bookmarks:send_message_to_participants')
        else:
            logger.error(f"Ошибки формы: {form.errors}")
            messages.error(request, f"Ошибка в форме: {form.errors}")
    else:
        form = SendMessageForm(user=request.user)

    return render(request, 'bookmarks/send_message.html', {'form': form})

@staff_member_required
def get_event_participants(request):
    event_id = request.GET.get('event_id')
    event_type = request.GET.get('event_type')
    
    if not event_id or not event_type:
        return JsonResponse({'error': 'Missing parameters'}, status=400)
        
    model_map = {
        'online': Events_online,
        'offline': Events_offline,
        'attractions': Attractions,
        'for_visiting': Events_for_visiting
    }
    
    model = model_map.get(event_type)
    if not model:
        return JsonResponse({'error': 'Invalid event type'}, status=400)
        
    try:
        event = model.objects.get(id=event_id)
        
        # Проверяем права доступа
        if not request.user.is_superuser and event.author != request.user:
            return JsonResponse({'error': 'Access denied'}, status=403)
            
        registered_users = Registered.objects.filter(**{event_type: event}).select_related('user')
        participants = [
            {
                'id': reg.user.id,
                'name': f"{reg.user.last_name} {reg.user.first_name} ({reg.user.username})"
            }
            for reg in registered_users
        ]
        return JsonResponse(participants, safe=False)
    except model.DoesNotExist:
        return JsonResponse({'error': 'Event not found'}, status=404)
