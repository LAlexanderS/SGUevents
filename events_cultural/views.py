import json
from django.http import JsonResponse
from django.shortcuts import render, get_list_or_404, get_object_or_404
from django.core.paginator import Paginator
from bookmarks.models import Favorite, Registered
from events_cultural.models import Attractions, Events_for_visiting
from bookmarks.models import Review
from events_cultural.utils import q_search_events_for_visiting, q_search_attractions
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import redirect
from users.models import User, Department
from datetime import datetime
from django.db.models import Q, CharField, Value
from django.db.models.functions import Concat
from django.utils.timezone import now
from django.core.paginator import EmptyPage, PageNotAnInteger


@login_required
def attractions(request):
    page = request.GET.get('page', 1)
    f_date = request.GET.get('f_date', None)
    f_tags = request.GET.getlist('f_tags', None)
    f_place = request.GET.get('f_place', None)
    order_by = request.GET.get('order_by', None)
    date_start = request.GET.get('date_start', None)
    date_end = request.GET.get('date_end', None)
    time_to_start = request.GET.get('time_to_start', None)
    time_to_end = request.GET.get('time_to_end', None)
    query = request.GET.get('q', None)  # Поиск через навигационную панель
    name_search = request.GET.get('name_search', None)  # Поиск только по названию через фильтр
    user = request.user

    # Получаем все достопримечательности
    all_info = Attractions.objects.all()

    # Получаем всех администраторов через отношение ManyToMany
    events_admin_set = set()
    for event in all_info:
        for admin in event.events_admin.all():
            events_admin_set.add(admin.get_full_name())
    events_admin = list(events_admin_set)

    filters_applied = False  # По умолчанию считаем, что фильтры не применены
    
    if name_search or query or date_start or date_end or time_to_start or time_to_end or f_tags:
        filters_applied = True

    # Фильтрация по названию
    if name_search:
        events_cultural = Attractions.objects.filter(name__icontains=name_search).order_by('-date_add')
        filters_applied = True
    elif query:
        # Полный поиск по названию и описанию через навигационную панель
        events_cultural = q_search_attractions(query)
        filters_applied = True
    else:
        # Если ни одного запроса нет, выводим все мероприятия, отсортированные по дате
        events_cultural = Attractions.objects.order_by('-date_add')

    # Фильтрация по скрытым мероприятиям
    if user.is_superuser or user.department.department_name in ['Administration', 'Superuser']:
        pass
    else:
        if user.department:
            events_cultural = events_cultural.filter(Q(secret__isnull=True) | Q(secret=user.department) | Q(member=user)).distinct()
        else:
            events_cultural = events_cultural.filter(secret__isnull=True).distinct()

    # Фильтрация по тегам
    if f_tags:
        tags_query = Q()
        for tag in f_tags:
            tags_query |= Q(tags__icontains=tag)
        events_cultural = events_cultural.filter(tags_query)
        filters_applied = True

    # Фильтрация по дате
    if date_start:
        date_start_formatted = datetime.strptime(date_start, '%d/%m/%Y').date()
        events_cultural = events_cultural.filter(date__gte=date_start_formatted)
        filters_applied = True

    if date_end:
        date_end_formatted = datetime.strptime(date_end, '%d/%m/%Y').date()
        events_cultural = events_cultural.filter(date__lte=date_end_formatted)
        filters_applied = True

    # Фильтрация по времени
    if time_to_start:
        time_start_formatted = datetime.strptime(time_to_start, '%H:%M').time()
        events_cultural = events_cultural.filter(time_start__gte=time_start_formatted)
        filters_applied = True

    if time_to_end:
        time_end_formatted = datetime.strptime(time_to_end, '%H:%M').time()
        events_cultural = events_cultural.filter(time_end__lte=time_end_formatted)
        filters_applied = True

    # Сортировка
    if order_by and order_by != "default":
        events_cultural = events_cultural.order_by(order_by)

    if f_place:
        events_cultural = events_cultural.annotate(
            full_place=Concat('town', Value(' '), 'street', Value(' '), 'house', output_field=CharField())
        ).filter(full_place__icontains=f_place)

    # Пагинация
    paginator = Paginator(events_cultural, 5)
    try:
        current_page = paginator.page(int(page))
    except PageNotAnInteger:
        # Если страница не является целым числом, возвращаем первую страницу
        current_page = paginator.page(1)
    except EmptyPage:
        # Если страница пуста (например, второй страницы не существует), возвращаем последнюю страницу
        current_page = paginator.page(paginator.num_pages)

    # Получаем избранные мероприятия пользователя
    favorites = Favorite.objects.filter(user=request.user, attractions__in=current_page)
    favorites_dict = {favorite.attractions.slug: favorite.id for favorite in favorites}

    # Получение отзывов
    reviews = {}
    for event in current_page:
        content_type = ContentType.objects.get_for_model(event)
        reviews[event.unique_id] = Review.objects.filter(content_type=content_type, object_id=event.id)

    results = Attractions.objects.annotate(
    full_address=Concat('town', Value(' '), 'street', Value(' '), 'house', output_field=CharField())
    ).values_list('full_address', flat=True)
    results = sorted(set(results))

    liked_slugs = [favorite.attractions.slug for favorite in favorites]

    tags = set()

    for event in all_info:
        if event.tags:
            split_tags = event.tags.split('#')
            for tag in split_tags:
                cleaned = tag.strip()
                if cleaned:
                    tags.add('#' + cleaned)

    tags = list(tags)


    context = {
        'name_page': 'Достопримечательности',
        'event_card_views': current_page,
        'favorites': favorites_dict,
        'reviews': reviews, 
        'events_admin': events_admin,
        'tags': tags,
        'time_to_start': time_to_start,
        'time_to_end': time_to_end,
        "date_start": date_start,
        "date_end": date_end,
        'filters_applied': filters_applied,
        "results":results,
        'now': now().date(),
        'liked': liked_slugs,

    }

    return render(request, 'events_cultural/attractions.html', context)


@login_required
def attractions_card(request, event_slug=False, event_id=False):
    reviews = {}
    if event_id:
        event = Attractions.objects.get(id=event_id)
    else:
        event = Attractions.objects.get(slug=event_slug)

    events = Attractions.objects.all()
    
    favorites = Favorite.objects.filter(user=request.user, attractions__in=events)
    favorites_dict = {favorite.attractions.slug: favorite.id for favorite in favorites}
    
    reviews = {}

    for event_rew in events:
        content_type = ContentType.objects.get_for_model(event)
        reviews[event_rew.unique_id] = Review.objects.filter(content_type=content_type, object_id=event.id)

    context = {
        'event': event,
        'reviews': reviews, 
        'favorites': favorites_dict,
        'now': now().date(),
    }
    return render(request, 'events_cultural/card.html', context=context)

@login_required
def events_for_visiting(request):
    page = request.GET.get('page', 1)
    f_events_for_visiting = request.GET.get('f_events_for_visiting', None)
    order_by = request.GET.get('order_by', None)
    query = request.GET.get('q', None)
    f_tags = request.GET.getlist('f_tags', None)
    date_start = request.GET.get('date_start', None)
    date_end = request.GET.get('date_end', None)
    time_to_start = request.GET.get('time_to_start', None)
    time_to_end = request.GET.get('time_to_end', None)
    query = request.GET.get('q', None)  # Поиск через навигационную панель
    name_search = request.GET.get('name_search', None)  # Поиск только по названию через фильтр
    f_date = request.GET.get('f_date', None)
    user = request.user
    
    


    all_info = Events_for_visiting.objects.all()
    
    # Получаем всех админов через отношение ManyToMany
    events_admin_set = set()
    for event in all_info:
        for admin in event.events_admin.all():
            events_admin_set.add(admin.get_full_name())

    events_admin = list(events_admin_set)

    filters_applied = False  # По умолчанию считаем, что фильтры не применены

    # Фильтрация по названию
    if name_search:
        events_cultural = Events_for_visiting.objects.filter(name__icontains=name_search).order_by('-date_add')
        filters_applied = True
    elif query:
        # Полный поиск по названию и описанию через навигационную панель
        events_cultural = q_search_events_for_visiting(query)
        filters_applied = True
    else:
        # Если ни одного запроса нет, выводим все мероприятия, отсортированные по дате
        events_cultural = Events_for_visiting.objects.order_by('-date_add')
    
    #Фильтрация по скрытым мероприятиям
    if user.is_superuser or user.department.department_name in ['Administration', 'Superuser']:
        pass 
    else:
        if user.department:
            events_cultural = events_cultural.filter(Q(secret__isnull=True) | Q(secret=user.department)).distinct()
        else:
            events_cultural = events_cultural.filter(secret__isnull=True).distinct()

    if order_by and order_by != "default":
        events_cultural = events_cultural.order_by(order_by)

    # Фильтрация по тегам
    if f_tags:
        tags_query = Q()
        for tag in f_tags:
            tags_query |= Q(tags__icontains=tag)
        events_cultural = events_cultural.filter(tags_query)
        filters_applied = True 

    # Фильтрация по дате
    if date_start:
        date_start_formatted = datetime.strptime(date_start, '%d/%m/%Y').date()
        events_cultural = events_cultural.filter(date__gte=date_start_formatted)
        filters_applied = True

    if date_end:
        date_end_formatted = datetime.strptime(date_end, '%d/%m/%Y').date()
        events_cultural = events_cultural.filter(date__lte=date_end_formatted)
        filters_applied = True

    # Фильтрация по времени
    if time_to_start:
        time_start_formatted = datetime.strptime(time_to_start, '%H:%M').time()
        events_cultural = events_cultural.filter(time_start__gte=time_start_formatted)
        filters_applied = True

    if time_to_end:
        time_end_formatted = datetime.strptime(time_to_end, '%H:%M').time()
        events_cultural = events_cultural.filter(time_end__lte=time_end_formatted)
        filters_applied = True
        
    # Сортировка
    if order_by and order_by != "default":
        events_cultural = events_cultural.order_by(order_by)
        
    paginator = Paginator(events_cultural, 5)
    try:
        current_page = paginator.page(int(page))
    except PageNotAnInteger:
        # Если страница не является целым числом, возвращаем первую страницу
        current_page = paginator.page(1)
    except EmptyPage:
        # Если страница пуста (например, второй страницы не существует), возвращаем последнюю страницу
        current_page = paginator.page(paginator.num_pages)

    favorites = Favorite.objects.filter(user=request.user, for_visiting__in=current_page)
    favorites_dict = {favorite.for_visiting.slug: favorite.id for favorite in favorites}

    registered = Registered.objects.filter(user=request.user, for_visiting__in=current_page)
    registered_dict = {reg.for_visiting.id: reg.id for reg in registered}

    reviews = {}
    for event in current_page:
        content_type = ContentType.objects.get_for_model(event)
        reviews[event.unique_id] = Review.objects.filter(content_type=content_type, object_id=event.id)

    liked_slugs = [favorite.for_visiting.slug for favorite in favorites]

    tags = set()

    for event in all_info:
        if event.tags:
            split_tags = event.tags.split('#')
            for tag in split_tags:
                cleaned = tag.strip()
                if cleaned:
                    tags.add('#' + cleaned)

    tags = list(tags)

    context = {
        'name_page': 'Доступные к посещению',
        'event_card_views': current_page,
        'favorites': favorites_dict,
        'registered': registered_dict,
        'reviews': reviews,
        'events_admin': events_admin,
        'tags': tags,
        'time_to_start': time_to_start,
        'time_to_end': time_to_end,
        "date_start": date_start,
        "date_end": date_end,
        'filters_applied': filters_applied,
        'now': now().date(),
        'liked': liked_slugs,
    }
    return render(request, 'events_cultural/events_for_visiting.html', context)

@login_required
def for_visiting_card(request, event_slug=False, event_id=False):
    if event_id:
        event = Events_for_visiting.objects.get(id=event_id)
    else:
        event = Events_for_visiting.objects.get(slug=event_slug)

    events = Events_for_visiting.objects.all()

    favorites = Favorite.objects.filter(user=request.user, for_visiting__in=events)
    favorites_dict = {favorite.for_visiting.slug: favorite.id for favorite in favorites}

    registered = Registered.objects.filter(user=request.user, for_visiting__in=events)
    registered_dict = {reg.for_visiting.id: reg.id for reg in registered}

    reviews = {}
    for event_rew in events:
        content_type = ContentType.objects.get_for_model(event)
        reviews[event_rew.unique_id] = Review.objects.filter(content_type=content_type, object_id=event.id)

    context = {
        'event': event,
        'reviews': reviews,
        'registered': registered_dict,
        'favorites': favorites_dict, 
        'now': now().date(),
    }
    return render(request, 'events_cultural/card.html', context=context)


def autocomplete_places(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        query = request.GET.get('term', '')
        places = Attractions.objects.filter(
            Q(town__icontains=query) | Q(street__icontains=query) | Q(house__icontains=query)).values_list('town', flat=True).distinct()
        places_list = list(places)
        return JsonResponse(places_list, safe=False)
    else:
        return JsonResponse({"error": "Invalid request"}, status=400)

@login_required
@csrf_exempt
def submit_review(request, event_id):
    if request.method == 'POST':
        comment = request.POST.get('comment', '')
        model_type = request.POST.get('model_type', '')

        if not comment:
            return JsonResponse({'success': False, 'message': 'Комментарий не может быть пустым'})

        if model_type == 'attractions':
            event = get_object_or_404(Attractions, id=event_id)
        elif model_type == 'for_visiting':
            event = get_object_or_404(Events_for_visiting, id=event_id)
        else:
            return JsonResponse({'success': False, 'message': 'Некорректный тип мероприятия'}, status=400)

        content_type = ContentType.objects.get_for_model(event)
        review = Review.objects.create(
            user=request.user,
            content_type=content_type,
            object_id=event.id,
            comment=comment
        )
        
        # Возвращаем данные о новом отзыве
        return JsonResponse({
            'success': True,
            'message': 'Отзыв добавлен',
            'formatted_date': review.formatted_date(),
            'review': {
                'user': {
                    'username': request.user.username,
                    'first_name': request.user.first_name,
                    'last_name': request.user.last_name
                },
                'comment': comment
            }
        })
    return JsonResponse({'success': False, 'message': 'Некорректный запрос'}, status=400)

@login_required
def index(request):
    return render(request, 'events_cultural/index.html')


def autocomplete_event_name(request):
    term = request.GET.get('term', '')  # Получаем параметр запроса
    is_attractions = request.GET.get('is_attractions', 'true')  # Указывает, в каком типе искать

    if is_attractions == 'true':  # Если поиск идет по Attractions
        matching_events = Attractions.objects.filter(name__icontains=term)[:10]
    else:  # Если поиск идет по Events_for_visiting
        matching_events = Events_for_visiting.objects.filter(name__icontains=term)[:10]

    suggestions = list(matching_events.values_list('name', flat=True))  # Преобразуем в список только имена
    return JsonResponse(suggestions, safe=False)