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


from main.utils import q_search_all
from users.models import User

@login_required
def index(request):
    available = Events_online.objects.order_by('date')
    available1 = Events_offline.objects.order_by('date')
    cultural = Attractions.objects.order_by('date')
    cultural1 = Events_for_visiting.objects.order_by('date')
    user = request.user

    if user.is_superuser or user.department.department_name not in ['Administration', 'Superuser']:
        all_content = list(chain(available, available1, cultural, cultural1))
    else:
        if user.department:
            available = available.filter(Q(secret__isnull=True) | Q(secret=user.department)).distinct()
            available1 = available1.filter(Q(secret__isnull=True) | Q(secret=user.department)).distinct()
            cultural = cultural.filter(Q(secret__isnull=True) | Q(secret=user.department)).distinct()
            cultural1 = cultural1.filter(Q(secret__isnull=True) | Q(secret=user.department)).distinct()
        else:
            available = available.filter(secret__isnull=True).distinct()
            available1 = available1.filter(secret__isnull=True).distinct()
            cultural = cultural.filter(secret__isnull=True).distinct()
            cultural1 = cultural1.filter(secret__isnull=True).distinct()
        
        all_content = list(chain(available, available1, cultural, cultural1))

    # Получаем всех спикеров из онлайн и оффлайн мероприятий
    speakers_online = User.objects.filter(speaker_online__in=available).distinct()
    speakers_offline = User.objects.filter(speaker_offline__in=available1).distinct()

    # Объединяем всех спикеров в один список (чтобы избежать дублирования)
    all_speakers = list(set(chain(speakers_online, speakers_offline)))

    page = request.GET.get('page', 1)
    f_all = request.GET.get('f_all', None)
    f_speakers = request.GET.getlist('f_speakers', None)
    f_tags = request.GET.getlist('f_tags', None)
    order_by = request.GET.get('order_by', None)
    query = request.GET.get('q', None)
    date_start = request.GET.get('date_start', None)
    date_end = request.GET.get('date_end', None)
    f_date = request.GET.get('f_date', None)

    # Фильтрация по запросу
    if not query:
        events_all = all_content
    else:
        events_all = q_search_all(query)

    # Фильтрация по дате
    if date_start:
        date_start_formatted = datetime.strptime(date_start, '%Y-%m-%d').date()
        events_all = [event for event in events_all if event.date >= date_start_formatted]

    if date_end:
        date_end_formatted = datetime.strptime(date_end, '%Y-%m-%d').date()
        events_all = [event for event in events_all if event.date <= date_end_formatted]

    # Фильтрация по спикерам
    if f_speakers:
        # Аннотируем пользователей полным именем
        speakers_with_full_name = User.objects.annotate(
            full_name=Concat('first_name', Value(' '), 'middle_name', Value(' '), 'last_name')
        )

        # Фильтруем пользователей по полным именам из f_speakers
        speakers_objects = speakers_with_full_name.filter(full_name__in=f_speakers)

        # Фильтруем только те события, которые имеют поле `speakers`
        events_all = [
            event for event in events_all
            if hasattr(event, 'speakers') and any(speaker in event.speakers.all() for speaker in speakers_objects)
        ]

    # Фильтрация по тегам
    if f_tags:
        events_all = [event for event in events_all if event.tags and any(tag in event.tags for tag in f_tags)]

    # Сортировка
    if order_by and order_by != "default":
        events_all = sorted(events_all, key=lambda x: getattr(x, order_by))

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
    'tags': list(set(tag for event in all_content if event.tags for tag in event.tags.split(','))),
    'f_tags': f_tags, 
    'speakers': all_speakers,
    'f_speakers': f_speakers,  
}

    return render(request, 'main/index.html', context)