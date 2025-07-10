from django.http import JsonResponse
from django.shortcuts import get_list_or_404, get_object_or_404, render
from bookmarks.models import Favorite, Registered
from events_available.models import Events_offline, Events_online
from django.core.paginator import Paginator
from events_available.utils import q_search_offline, q_search_online, q_search_name_offline
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.contenttypes.models import ContentType
from bookmarks.models import Review
from users.models import Department, User
from django.db.models import Q
from django.db.models import CharField, Value, F
from django.db.models.functions import Concat
from django.utils.timezone import now
from django.core.paginator import EmptyPage, PageNotAnInteger
from django.db.models import Avg



@login_required
def online(request):
    page = request.GET.get('page', 1)
    f_date = request.GET.get('f_date', None)
    f_speakers = request.GET.getlist('f_speakers[]', None)
    f_tags = request.GET.getlist('f_tags[]', None)
    order_by = request.GET.get('order_by', None)
    date_start = request.GET.get('date_start', None)
    date_end = request.GET.get('date_end', None)
    time_to_start = request.GET.get('time_to_start', None)
    time_to_end = request.GET.get('time_to_end', None)
    # sort_time = request.GET.get('sort_time', 'default') 
    # sort_date = request.GET.get('sort_date', 'default')  
    query = request.GET.get('q', None)  # Поиск через навигационную панель
    name_search = request.GET.get('name_search', None)  # Поиск только по названию через фильтр
    user = request.user

    all_info = Events_online.objects.all()
    # Получаем всех спикеров через отношение ManyToMany
    speakers_set = set()
    for event in all_info:
        for speaker in event.speakers.all():
            # Явно формируем строку с Фамилией, Именем и Отчеством
            full_name = f"{speaker.last_name} {speaker.first_name} {speaker.middle_name if speaker.middle_name else ''}".strip()
            speakers_set.add(full_name)

    speakers = list(speakers_set)


    # Получаем всех админов через отношение ManyToMany
    events_admin_set = set()
    for event in all_info:
        for admin in event.events_admin.all():
            events_admin_set.add(f"{admin.last_name} {admin.first_name}")

    events_admin = list(events_admin_set)
    
    filters_applied = False  # По умолчанию считаем, что фильтры не применен

    if name_search:
        # Фильтр только по названию
        events_available = Events_online.objects.filter(name__icontains=name_search)
        filters_applied = True
    elif query:
        # Полный поиск по названию и описанию через навигационную панель
        events_available = q_search_online(query)
        filters_applied = True
    else:
        # Если ни одного запроса нет, выводим все мероприятия, отсортированные по дате
        events_available = Events_online.objects.all()

    #Фильтрация по скрытым мероприятиям
    if user.is_superuser or user.department.department_name in ['Administration', 'Superuser']:
        pass 
    else:
        if user.department:
            events_available = events_available.filter(Q(secret__isnull=True) | Q(secret=user.department) | Q(member=user)).distinct()
        else:
            events_available = events_available.filter(secret__isnull=True).distinct()  

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
            events_available = events_available.filter(speakers__in=speakers_objects)

    if f_tags:
        tags_query = Q()
        for tag in f_tags:
            tags_query |= Q(tags__icontains=tag)
        events_available = events_available.filter(tags_query)

    if order_by and order_by != "default":
        events_available = events_available.order_by(order_by)
    else:
        events_available = events_available.order_by('-date_add')

    
    if date_start:
        date_start_formatted = datetime.strptime(date_start, '%Y-%m-%d').date()
        events_available = events_available.filter(date__gte=date_start_formatted)

    if date_end:
        date_end_formatted = datetime.strptime(date_end, '%Y-%m-%d').date()
        events_available = events_available.filter(date__lte=date_end_formatted)


        # Фильтрация по времени начала
    if time_to_start:
        time_start_formatted = datetime.strptime(time_to_start, '%H:%M').time()  # Преобразование строки в объект времени
        events_available = events_available.filter(time_start__gte=time_start_formatted)

    # Фильтрация по времени окончания
    if time_to_end:
        time_end_formatted = datetime.strptime(time_to_end, '%H:%M').time()  # Преобразование строки в объект времени
        events_available = events_available.filter(time_end__lte=time_end_formatted)

    paginator = Paginator(events_available, 5)
    try:
        current_page = paginator.page(int(page))
    except PageNotAnInteger:
        # Если страница не является целым числом, возвращаем первую страницу
        current_page = paginator.page(1)
    except EmptyPage:
        # Если страница пуста (например, второй страницы не существует), возвращаем последнюю страницу
        current_page = paginator.page(paginator.num_pages)

    favorites = Favorite.objects.filter(user=request.user, online__in=current_page)
    favorites_dict = {favorite.online.slug: favorite.id for favorite in favorites}


    registered = Registered.objects.filter(user=request.user, online__in=current_page)
    registered_dict = {reg.online.id: reg.id for reg in registered}

    reviews = {}
    for event in current_page:
        content_type = ContentType.objects.get_for_model(event)
        reviews[event.unique_id] = Review.objects.filter(content_type=content_type, object_id=event.id)

    liked_slugs = [favorite.online.slug for favorite in favorites]
    
    tags = set()

    for event in all_info:
        if event.tags:
            split_tags = event.tags.split('#')
            for tag in split_tags:
                cleaned = tag.strip()
                if cleaned:
                    tags.add('#' + cleaned)

    tags = list(tags)

    reviews_avg = {}
    for event in events_available:
        content_type = ContentType.objects.get_for_model(event)
        avg_rating = Review.objects.filter(
            content_type=content_type,
            object_id=event.id,
            rating__isnull=False
        ).aggregate(Avg('rating'))['rating__avg']
        reviews_avg[event.id] = round(avg_rating, 1) if avg_rating else 0

    context = {
        'name_page': 'Онлайн',
        'event_card_views': current_page,
        'speakers': speakers,
        'events_admin': events_admin,
        'tags': tags,
        'favorites': favorites_dict,
        'registered': registered_dict,
        'reviews': reviews,
        'time_to_start': time_to_start,
        'time_to_end': time_to_end,
        "date_start": date_start,
        "date_end": date_end,
        'filters_applied': filters_applied,
        'now': now().date(),
        'liked': liked_slugs,
        'reviews_avg': reviews_avg,
    }

    return render(request, 'events_available/online_events.html', context=context)


@login_required
def online_card(request, event_slug=False, event_id=False):
    reviews = {}
    if event_id:
        event = Events_online.objects.get(id=event_id)
    else:
        event = Events_online.objects.get(slug=event_slug)

    events = Events_online.objects.all()
    
    reviews = {}

    for event_rew in events:
        content_type = ContentType.objects.get_for_model(event)
        reviews[event_rew.unique_id] = Review.objects.filter(content_type=content_type, object_id=event.id)

    favorites = Favorite.objects.filter(user=request.user, online__in=events)
    favorites_dict = {favorite.online.slug: favorite.id for favorite in favorites}

    registered = Registered.objects.filter(user=request.user, online__in=events)
    registered_dict = {reg.online.id: reg.id for reg in registered}

    rev = Review.objects.all()
    for rr in rev:
        print(f'idd {rr.id}')
    reviews_avg = {}
    for avg in events:
        content_type = ContentType.objects.get_for_model(avg)
        print(f'sssssssssssss {avg.id}')



        avg_rating = Review.objects.filter(
            content_type=content_type,
            object_id=avg.id,
            rating__isnull=False
        ).aggregate(Avg('rating'))['rating__avg']
        reviews_avg[avg.id] = round(avg_rating, 1) if avg_rating else 0

    context = {
        'event': event,
        'reviews': reviews, 
        'registered': registered_dict,
        'favorites': favorites_dict,
        'now': now().date(),
        'reviews_avg': reviews_avg,
    }
    
    return render(request, 'events_available/card.html', context=context)


@login_required
def offline(request):
    page = request.GET.get('page', 1)
    f_date = request.GET.getlist('f_date', None)
    f_speakers = request.GET.getlist('f_speakers', None)
    f_tags = request.GET.getlist('f_tags', None)
    f_place = (
    request.GET.get('f_place') or
    request.GET.get('place_search') or
    request.GET.get('term')
    )
    order_by = request.GET.get('order_by', None)
    query = request.GET.get('q', None)
    query_name = request.GET.get('qn', None)
    date_start = request.GET.get('date_start', None)
    date_end = request.GET.get('date_end', None)
    time_to_start = request.GET.get('time_to_start', None)
    time_to_end = request.GET.get('time_to_end', None)
    name_search = request.GET.get('name_search', None)  # Поиск только по названию через фильтр
    user = request.user

    today = now().date()
    
    all_info = Events_offline.objects.all()
    # Получаем всех спикеров
    speakers_set = set()
    for event in all_info:
        for speaker in event.speakers.all():
            # Явно формируем строку с Фамилией, Именем и Отчеством
            full_name = f"{speaker.last_name} {speaker.first_name} {speaker.middle_name if speaker.middle_name else ''}".strip()
            speakers_set.add(full_name)

    speakers = list(speakers_set)

    # Получаем всех админов через отношение ManyToMany
    events_admin_set = set()
    for event in all_info:
        for admin in event.events_admin.all():
            events_admin_set.add(admin.get_full_name())

    events_admin = list(events_admin_set)

    filters_applied = False  # По умолчанию считаем, что фильтры не применен

    if name_search:
        # Фильтр только по названию
        events_available = Events_offline.objects.filter(name__icontains=name_search)
        filters_applied = True
    elif query:
        # Полный поиск по названию и описанию через навигационную панель
        events_available = q_search_offline(query)
        filters_applied = True
    else:
        # Если ни одного запроса нет, выводим все мероприятия, отсортированные по дате
        events_available = Events_offline.objects.all()

    #Фильтрация по скрытым мероприятиям
    if user.is_superuser or user.department.department_name in ['Administration', 'Superuser']:
        pass 
    else:
        if user.department:
            events_available = events_available.filter(Q(secret__isnull=True) | Q(secret=user.department) | Q(member=user)).distinct()
        else:
            events_available = events_available.filter(secret__isnull=True).distinct()


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
            events_available = events_available.filter(speakers__in=speakers_objects)

    if f_tags:
        tags_query = Q()
        for tag in f_tags:
            tags_query |= Q(tags__icontains=tag)
        events_available = events_available.filter(tags_query)

    if order_by and order_by != "default":
        events_available = events_available.order_by(order_by)
    else:
        events_available = events_available.order_by('-date_add')

    if date_start:
        date_start_formatted = datetime.strptime(date_start, '%Y-%m-%d').date()
        events_available = events_available.filter(date__gte=date_start_formatted)

    if date_end:
        date_end_formatted = datetime.strptime(date_end, '%Y-%m-%d').date()
        events_available = events_available.filter(date__lte=date_end_formatted)

        # Фильтрация по времени начала
    if time_to_start:
        time_start_formatted = datetime.strptime(time_to_start, '%H:%M').time()  # Преобразование строки в объект времени
        events_available = events_available.filter(time_start__gte=time_start_formatted)

    # Фильтрация по времени окончания
    if time_to_end:
        time_end_formatted = datetime.strptime(time_to_end, '%H:%M').time()  # Преобразование строки в объект времени
        events_available = events_available.filter(time_end__lte=time_end_formatted)


    if f_place:
        events_available = events_available.annotate(
            full_place=Concat(
                F('town'), Value(' '),
                F('street'), Value(' '),
                F('house'), Value(' '),
                F('cabinet'),
                output_field=CharField()
            )
        ).filter(full_place__icontains=f_place)

    paginator = Paginator(events_available, 5)
    try:
        current_page = paginator.page(int(page))
    except PageNotAnInteger:
        # Если страница не является целым числом, возвращаем первую страницу
        current_page = paginator.page(1)
    except EmptyPage:
        # Если страница пуста (например, второй страницы не существует), возвращаем последнюю страницу
        current_page = paginator.page(paginator.num_pages)

    favorites = Favorite.objects.filter(user=request.user, offline__in=current_page)
    favorites_dict = {favorite.offline.slug: favorite.id for favorite in favorites}

    registered = Registered.objects.filter(user=request.user, offline__in=current_page)
    registered_dict = {reg.offline.id: reg.id for reg in registered}

    reviews = {}
    for event in current_page:
        content_type = ContentType.objects.get_for_model(event)
        reviews[event.unique_id] = Review.objects.filter(content_type=content_type, object_id=event.id)

    results = Events_offline.objects.annotate(
    full_address=Concat('town', Value(' '), 'street', Value(' '), 'house', Value(' '), 'cabinet', output_field=CharField())
    ).values_list('full_address', flat=True)
    results = sorted(set(results))

    liked_slugs = [favorite.offline.slug for favorite in favorites]

    tags = set()

    for event in all_info:
        if event.tags:
            split_tags = event.tags.split('#')
            for tag in split_tags:
                cleaned = tag.strip()
                if cleaned:
                    tags.add('#' + cleaned)

    tags = list(tags)
   
    reviews_avg = {}
    for event in events_available:
        content_type = ContentType.objects.get_for_model(event)
        avg_rating = Review.objects.filter(
            content_type=content_type,
            object_id=event.id,
            rating__isnull=False
        ).aggregate(Avg('rating'))['rating__avg']
        reviews_avg[event.id] = round(avg_rating, 1) if avg_rating else 0

    context = {
        'name_page': 'Оффлайн',
        'event_card_views': current_page,
        'speakers': speakers,
        'events_admin': events_admin,
        'tags': tags,
        'favorites': favorites_dict,
        'registered': registered_dict,
        'reviews': reviews,
        "results":results,
        'time_to_start': time_to_start,
        'time_to_end': time_to_end,
        "date_start": date_start,
        "date_end": date_end,
        'filters_applied': filters_applied,
        'now': now().date(),
        'liked': liked_slugs,
        'reviews_avg': reviews_avg,
    }

    return render(request, 'events_available/offline_events.html', context=context)

@login_required
def offline_card(request, event_slug=False, event_id=False):
    if event_id:
        event = Events_offline.objects.get(id=event_id)
    else:
        event = Events_offline.objects.get(slug=event_slug)

    events = Events_offline.objects.all()
    
    reviews = {}

    for event_rew in events:
        content_type = ContentType.objects.get_for_model(event)
        reviews[event_rew.unique_id] = Review.objects.filter(content_type=content_type, object_id=event.id)

    favorites = Favorite.objects.filter(user=request.user, offline__in=events)
    favorites_dict = {favorite.offline.slug: favorite.id for favorite in favorites}
    
    registered = Registered.objects.filter(user=request.user, offline__in=events)
    registered_dict = {reg.offline.id: reg.id for reg in registered}

    rev = Review.objects.all()
    for rr in rev:
        print(f'idd {rr.id}')
    reviews_avg = {}
    for avg in events:
        content_type = ContentType.objects.get_for_model(avg)
        print(f'sssssssssssss {avg.id}')



        avg_rating = Review.objects.filter(
            content_type=content_type,
            object_id=avg.id,
            rating__isnull=False
        ).aggregate(Avg('rating'))['rating__avg']
        reviews_avg[avg.id] = round(avg_rating, 1) if avg_rating else 0

    context = {
        'event': event,
        'reviews': reviews, 
        'registered': registered_dict,
        'favorites': favorites_dict,
        'now': now().date(),
        'reviews_avg': reviews_avg,
    }

    return render(request, 'events_available/card.html', context=context)

def autocomplete_places(request):
    query = request.GET.get('term', '')
    if not query:
        return JsonResponse([], safe=False)

    places = Events_offline.objects.annotate(
        full_address=Concat(
            F('town'), Value(' '),
            F('street'), Value(' '),
            F('house'), Value(' '),
            F('cabinet'),
            output_field=CharField()
        )
    ).filter(
        Q(town__icontains=query) |
        Q(street__icontains=query) |
        Q(house__icontains=query) |
        Q(cabinet__icontains=query)
    ).values_list('full_address', flat=True).distinct()[:10]

    return JsonResponse(list(places), safe=False) 

@login_required
@csrf_exempt
def submit_review(request, event_id):
    if request.method == 'POST':
        comment = request.POST.get('comment', '')
        rating = request.POST.get('rating')
        model_type = request.POST.get('model_type', '')

        if not comment:
            return JsonResponse({'success': False, 'message': 'Комментарий не может быть пустым'})

        if model_type == 'offline':
            event = get_object_or_404(Events_offline, id=event_id)
        elif model_type == 'online':
            event = get_object_or_404(Events_online, id=event_id)
        else:
            return JsonResponse({'success': False, 'message': 'Некорректный тип мероприятия'}, status=400)

        content_type = ContentType.objects.get_for_model(event)

        print(f'Рейтинг в submit_review {rating}')
        review = Review.objects.create(
                user=request.user,
                content_type=content_type,
                object_id=event.id,
                comment=comment,
                rating=int(rating) if rating else None
            )
        
        # Считаем новое среднее значение
        avg_rating = Review.objects.filter(
            content_type=content_type,
            object_id=event.id,
            rating__isnull=False
        ).aggregate(Avg('rating'))['rating__avg']
        avg_rating = round(avg_rating, 1) if avg_rating else 0

        print(f'qqqqqqqqqqq {avg_rating}')

        # # Проверяем, существует ли уже отзыв от этого пользователя
        # existing_review = Review.objects.filter(
        #     user=request.user,
        #     content_type=content_type,
        #     object_id=event.id
        # ).first()

        # if existing_review:
        #     # Обновляем существующий отзыв
        #     if comment:
        #         existing_review.comment = comment
        #     if rating:
        #         existing_review.rating = int(rating)
        #     existing_review.save()
        #     review = existing_review
        # else:
        #     # Создаем новый отзыв
        #     review = Review.objects.create(
        #         user=request.user,
        #         content_type=content_type,
        #         object_id=event.id,
        #         comment=comment,
        #         rating=int(rating) if rating else None
        #     )
        
        # Возвращаем данные о новом отзыве
        return JsonResponse({
            'success': True,
            'message': 'Отзыв добавлен',
            'formatted_date': review.formatted_date(),
            'new_avg': avg_rating,
            'review': {
                'user': {
                    'username': request.user.username,
                    'first_name': request.user.first_name,
                    'last_name': request.user.last_name
                },
                'comment': comment,
                'rating': review.rating
            }
        })
    return JsonResponse({'success': False, 'message': 'Некорректный запрос'}, status=400)



def autocomplete_event_name(request):
    term = request.GET.get('term', '')  # Получаем параметр запроса
    is_online = request.GET.get('is_online', 'true')  # Получаем параметр, который указывает, онлайн это мероприятие или оффлайн

    if is_online == 'true':
        matching_events = Events_online.objects.filter(name__icontains=term)[:10]  # Поиск в онлайн мероприятиях
    else:
        matching_events = Events_offline.objects.filter(name__icontains=term)[:10]  # Поиск в оффлайн мероприятиях

    suggestions = list(matching_events.values_list('name', flat=True))  # Преобразуем в список только имена
    return JsonResponse(suggestions, safe=False)





