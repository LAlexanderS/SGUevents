from django.shortcuts import get_list_or_404, get_object_or_404, render
from django.core.paginator import Paginator
from bookmarks.models import Favorite, Registered, Review
from events_available.models import Events_offline, Events_online
from events_cultural.models import Attractions, Events_for_visiting
from itertools import chain
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from datetime import datetime
from django.db.models import Value
from django.db.models.functions import Concat
from events_available.utils import *
from events_cultural.utils import *
from django.http import JsonResponse
from django.utils.timezone import now


from main.utils import q_search_all
from users.models import User

@login_required
def index(request):
    page = request.GET.get('page', 1)
    f_all = request.GET.get('f_all', None)
    f_speakers = request.GET.getlist('f_speakers', None)
    f_tags = request.GET.getlist('f_tags', None)
    order_by = request.GET.get('order_by', None)
    query = request.GET.get('q', None)
    date_start = request.GET.get('date_start', None)
    date_end = request.GET.get('date_end', None)
    f_date = request.GET.get('f_date', None)
    name_search = request.GET.get('name_search', None)  # Поиск только по названию через фильтр
    time_to_start = request.GET.get('time_to_start', None)
    time_to_end = request.GET.get('time_to_end', None)
    available = Events_online.objects.order_by('date')
    available1 = Events_offline.objects.order_by('date')
    cultural = Attractions.objects.order_by('date')
    cultural1 = Events_for_visiting.objects.order_by('date')
    user = request.user
    page = request.GET.get('page', 1)
    f_speakers = request.GET.getlist('f_speakers', None)

    # СПИКЕРЫ
    speakers_set = set()
    for event in available:
        for speaker in event.speakers.all():
            # Явно формируем строку с Фамилией, Именем и Отчеством
            full_name = f"{speaker.last_name} {speaker.first_name} {speaker.middle_name if speaker.middle_name else ''}".strip()
            speakers_set.add(full_name)

    for event in available1:
        for speaker in event.speakers.all():
            # Явно формируем строку с Фамилией, Именем и Отчеством
            full_name = f"{speaker.last_name} {speaker.first_name} {speaker.middle_name if speaker.middle_name else ''}".strip()
            speakers_set.add(full_name)

    speakers = list(speakers_set)

    # СКРЫТЫЕ
    if user.is_superuser or user.department.department_name in ['Administration', 'Superuser']:
        events_all = list(chain(available, available1, cultural, cultural1))
    else:
        if user.department:
            available = available.filter(Q(secret__isnull=True) | Q(secret=user.department) | Q(member=user)).distinct()
            available1 = available1.filter(Q(secret__isnull=True) | Q(secret=user.department) | Q(member=user)).distinct()
            cultural = cultural.filter(Q(secret__isnull=True) | Q(secret=user.department) | Q(member=user)).distinct()
            cultural1 = cultural1.filter(Q(secret__isnull=True) | Q(secret=user.department) | Q(member=user)).distinct()
        else:
            available = available.filter(secret__isnull=True).distinct()
            available1 = available1.filter(secret__isnull=True).distinct()
            cultural = cultural.filter(secret__isnull=True).distinct()
            cultural1 = cultural1.filter(secret__isnull=True).distinct()
        
        events_all = list(chain(available, available1, cultural, cultural1))

    # Получаем всех админов через отношение ManyToMany
    events_admin_set = set()
    for event in events_all:
        for admin in event.events_admin.all():
            events_admin_set.add(admin.get_full_name())

    events_admin = list(events_admin_set)

    filters_applied = False  # По умолчанию считаем, что фильтры не применен

    if name_search:
        # Фильтр только по названию
        available = Events_online.objects.filter(name__icontains=name_search).order_by('-date_add')
        available1 = Events_offline.objects.filter(name__icontains=name_search).order_by('-date_add')
        cultural = Attractions.objects.filter(name__icontains=name_search).order_by('-date_add')
        cultural1 = Events_for_visiting.objects.filter(name__icontains=name_search).order_by('-date_add')
        events_all = list(chain(available, available1, cultural, cultural1))
        filters_applied = True
    elif query:
        # Полный поиск по названию и описанию через навигационную панель
        available = q_search_online(query)
        available1 = q_search_offline(query)
        cultural = q_search_attractions(query)
        cultural1 = q_search_events_for_visiting(query)
        filters_applied = True
        events_all = list(chain(available, available1, cultural, cultural1))
    else:
        # Если ни одного запроса нет, выводим все мероприятия, отсортированные по дате
        available = Events_online.objects.order_by('-date_add')
        available1 = Events_online.objects.order_by('-date_add')
        cultural = Events_online.objects.order_by('-date_add')
        cultural1 = Events_online.objects.order_by('-date_add')

    # Фильтрация по дате
    if date_start:
        date_start_formatted = datetime.strptime(date_start, '%d/%m/%Y').date()
        events_all = [event for event in events_all if event.date >= date_start_formatted]

    if date_end:
        date_end_formatted = datetime.strptime(date_end, '%d/%m/%Y').date()
        events_all = [event for event in events_all if event.date <= date_end_formatted]

        # Фильтрация по времени начала
    if time_to_start:
        time_start_formatted = datetime.strptime(time_to_start, '%H:%M').time()  # Преобразование строки в объект времени
        events_all = [event for event in events_all if event.time_start >= time_start_formatted]
        

    # Фильтрация по времени окончания
    if time_to_end:
        time_end_formatted = datetime.strptime(time_to_end, '%H:%M').time()  # Преобразование строки в объект времени
        events_all = [event for event in events_all if event.time_end <= time_end_formatted]
        

    # Инициализируем пустой список для спикеров, чтобы избежать ошибки, если фильтры по спикерам не применяются
    speakers_objects = []

     # Фильтрация по спикерам
    if f_speakers:
        # Преобразуем имена спикеров в объекты User, учитывая Фамилию, Имя, и Отчество
        for name in f_speakers:
            # Разбиваем на части: Фамилия Имя Отчество
            split_name = name.split()
            
            if len(split_name) == 2:  # Если есть только фамилия и имя
                last_name, first_name = split_name
                users = User.objects.filter(
                    first_name=first_name,
                    last_name=last_name
                )
                speakers_objects.extend(users)
            
            elif len(split_name) == 3:  # Если есть фамилия, имя и отчество
                last_name, first_name, middle_name = split_name
                users = User.objects.filter(
                    first_name=first_name,
                    middle_name=middle_name,
                    last_name=last_name
                )
                speakers_objects.extend(users)
        
        # Применяем фильтр по спикерам, если есть результаты
        if speakers_objects:
            available1 = available1.filter(speakers__in=speakers_objects)
            available = available.filter(speakers__in=speakers_objects)

            events_all = list(chain(available, available1))

    # Фильтрация по тегам
    if f_tags:
        events_all = [event for event in events_all if event.tags and any(tag in event.tags for tag in f_tags)]

    # Сортировка
    if order_by and order_by != "default":
        reverse = False  # По умолчанию сортировка по возрастанию
        if order_by.startswith('-'):
            reverse = True
            order_by = order_by[1:]  # Убираем знак минуса для обратной сортировки

        events_all = sorted(events_all, key=lambda x: getattr(x, order_by), reverse=reverse)


    # Пагинация
    paginator = Paginator(events_all, 10)
    current_page = paginator.page(int(page))

    current_online = [event for event in current_page if isinstance(event, Events_online)]
    current_offline = [event for event in current_page if isinstance(event, Events_offline)]
    current_attractions = [event for event in current_page if isinstance(event, Attractions)]
    current_for_visiting = [event for event in current_page if isinstance(event, Events_for_visiting)]

    favorites_online = Favorite.objects.filter(user=request.user, online__in=current_online).values_list('online_id', 'id')
    favorites_offline = Favorite.objects.filter(user=request.user, offline__in=current_offline).values_list('offline_id', 'id')
    favorites_attractions = Favorite.objects.filter(user=request.user, attractions__in=current_attractions).values_list('attractions_id', 'id')
    favorites_for_visiting = Favorite.objects.filter(user=request.user, for_visiting__in=current_for_visiting).values_list('for_visiting_id', 'id')

    favorites_dict = {
        'online': {item[0]: item[1] for item in favorites_online},
        'offline': {item[0]: item[1] for item in favorites_offline},
        'attractions': {item[0]: item[1] for item in favorites_attractions},
        'for_visiting': {item[0]: item[1] for item in favorites_for_visiting},
    }

    registered_online = Registered.objects.filter(user=request.user, online__in=current_online).values_list('online_id', 'id')
    registered_offline = Registered.objects.filter(user=request.user, offline__in=current_offline).values_list('offline_id', 'id')
    registered_attractions = Registered.objects.filter(user=request.user, attractions__in=current_attractions).values_list('attractions_id', 'id')
    registered_for_visiting = Registered.objects.filter(user=request.user, for_visiting__in=current_for_visiting).values_list('for_visiting_id', 'id')

    registered_dict = {
        'online': {item[0]: item[1] for item in registered_online},
        'offline': {item[0]: item[1] for item in registered_offline},
        'attractions': {item[0]: item[1] for item in registered_attractions},
        'for_visiting': {item[0]: item[1] for item in registered_for_visiting},
    }

    reviews = {}
    for event in current_page:
        content_type = ContentType.objects.get_for_model(event)
        reviews[event.unique_id] = Review.objects.filter(content_type=content_type, object_id=event.id)

    context = {
    'name_page': 'Главная',
    'event_card_views': current_page,
    'favorites': favorites_dict,
    'reviews': reviews,
    'registered': registered_dict,
    'tags': list(set(tag for event in events_all if event.tags for tag in event.tags.split(','))),
    'f_tags': f_tags, 
    'speakers': speakers,
    'f_speakers': f_speakers,  
    'filters_applied': filters_applied,
    'time_to_start': time_to_start,
    'time_to_end': time_to_end,
    "date_start": date_start,
    "date_end": date_end,
    'now': now().date(),

}

    return render(request, 'main/index.html', context)

import logging
logger = logging.getLogger(__name__)

def autocomplete_event_name(request):
    term = request.GET.get('term', '')  # Получаем параметр запроса
    if not term:
        return JsonResponse([], safe=False)

    try:
        # Ищем совпадения по всем типам мероприятий
        matching_online = Events_online.objects.filter(name__icontains=term)[:10]
        matching_offline = Events_offline.objects.filter(name__icontains=term)[:10]
        matching_attractions = Attractions.objects.filter(name__icontains=term)[:10]
        matching_for_visiting = Events_for_visiting.objects.filter(name__icontains=term)[:10]

        # Объединяем все события
        all_matching_events = list(chain(matching_online, matching_offline, matching_attractions, matching_for_visiting))

        # Извлекаем названия мероприятий
        suggestions = [event.name for event in all_matching_events]

        return JsonResponse(suggestions, safe=False)

    except Exception as e:
        return JsonResponse([], safe=False)