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

    context = {
        'events': events,
        'reviews': reviews,
        'favorites': favorites,
        'registered': registered_dict,
        'now': now().date(),
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
        if created and event_type == 'for_visiting':
                # Уменьшаем количество свободных мест
                event.place_free -= 1
                event.save(update_fields=['place_free'])
                print(f'Free places after registration: {event.place_free}')

        if created and event_type == 'for_visiting':
            return JsonResponse({'added': True, 'event_id': registered.id, 'event_slug': event_slug, 'place_free': event.place_free})
        elif created and event_type != 'for_visiting':
            return JsonResponse({'added': True, 'event_id': registered.id, 'event_slug': event_slug})
        else:
            return JsonResponse({'added': False, 'error': 'Already registered'}, status=400)

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
            event.for_visiting.place_free += 1
            event.for_visiting.save(update_fields=['place_free'])
            print(f'Free places after unregister: {event.for_visiting.place_free}')

        event.delete()
        telegram_id = request.user.telegram_id
        if telegram_id:
            message = f"\U0000274C Вы успешно отменили регистрацию на мероприятие: {event_name}"
            send_message_to_user(telegram_id, message)
        
        if event.for_visiting:
            return JsonResponse({'removed': True, 'event_name': event_name, 'event_slug': event_slug, 'place_free': event.for_visiting.place_free})
        else:
            return JsonResponse({'removed': True, 'event_slug': event_slug, 'event_name': event_name})

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

    for reg in registered:
        if reg.online:
            events.append(reg.online)
            online_ids.append(reg.online.id)
        elif reg.offline:
            events.append(reg.offline)
            offline_ids.append(reg.offline.id)
        elif reg.attractions:
            events.append(reg.attractions)
            attractions_ids.append(reg.attractions.id)
        elif reg.for_visiting:
            events.append(reg.for_visiting)
            for_visiting_ids.append(reg.for_visiting.id)

    for event in events:
        content_type = ContentType.objects.get_for_model(event)
        reviews[event.unique_id] = Review.objects.filter(content_type=content_type, object_id=event.id)

    favorites_online = Favorite.objects.filter(user=request.user, online_id__in=online_ids).values_list('online_id', 'id')
    favorites_offline = Favorite.objects.filter(user=request.user, offline_id__in=offline_ids).values_list('offline_id', 'id')
    favorites_attractions = Favorite.objects.filter(user=request.user, attractions_id__in=attractions_ids).values_list('attractions_id', 'id')
    favorites_for_visiting = Favorite.objects.filter(user=request.user, for_visiting_id__in=for_visiting_ids).values_list('for_visiting_id', 'id')

    favorites_dict = {
        'online': {item[0]: item[1] for item in favorites_online},
        'offline': {item[0]: item[1] for item in favorites_offline},
        'attractions': {item[0]: item[1] for item in favorites_attractions},
        'for_visiting': {item[0]: item[1] for item in favorites_for_visiting},
    }

    context = {
        'registered': registered,
        'reviews': reviews,
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
        event_type = request.POST.get('event_type')  # Получаем тип мероприятия из POST-запроса
        form = SendMessageForm(request.POST, event_type=event_type)
        if form.is_valid():
            event = form.cleaned_data['event']
            message = form.cleaned_data['message']

            if not event:
                messages.error(request, "Пожалуйста, выберите мероприятие.")
                return redirect('bookmarks:send_message_to_participants')

            # Получаем всех зарегистрированных участников для данного мероприятия
            registered_users = Registered.objects.filter(**{event_type: event})

            if not registered_users.exists():
                messages.error(request, "Нет зарегистрированных участников для выбранного мероприятия.")
                return redirect('bookmarks:send_message_to_participants')

            for registration in registered_users:
                if registration.user.telegram_id and registration.notifications_enabled:
                    send_notification_with_toggle(
                        telegram_id=registration.user.telegram_id,
                        message=message,
                        event_id=event.unique_id,
                        notifications_enabled=registration.notifications_enabled
                    )
            messages.success(request, "Сообщения успешно отправлены участникам.")
            return redirect('bookmarks:send_message_to_participants')
    else:
        form = SendMessageForm()

    return render(request, 'bookmarks/send_message.html', {'form': form})
