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
from django.db.models import CharField, Value
from django.db.models.functions import Concat



@login_required
def online(request):
    page = request.GET.get('page', 1)
    f_date = request.GET.get('f_date', None)
    f_speakers = request.GET.getlist('f_speakers', None)
    f_tags = request.GET.getlist('f_tags', None)
    order_by = request.GET.get('order_by', None)
    date_start = request.GET.get('date_start', None)
    date_end = request.GET.get('date_end', None)
    time_to_start = request.GET.get('time_to_start', None)
    time_to_end = request.GET.get('time_to_end', None)
    query = request.GET.get('q', None)
    user = request.user

    all_info = Events_online.objects.all()
    # Получаем всех спикеров через отношение ManyToMany
    speakers_set = set()
    for event in all_info:
        for speaker in event.speakers.all():
            speakers_set.add(speaker.get_full_name())

    speakers = list(speakers_set)

    # Получаем всех админов через отношение ManyToMany
    events_admin_set = set()
    for event in all_info:
        for admin in event.events_admin.all():
            events_admin_set.add(admin.get_full_name())

    events_admin = list(events_admin_set)
    
    if not query:
        events_available = Events_online.objects.order_by('date')
    else:
        events_available = q_search_online(query)

    #Фильтрация по скрытым мероприятиям
    if user.is_superuser or user.department.department_name in ['Administration', 'Superuser']:
        pass 
    else:
        if user.department:
            events_available = events_available.filter(Q(secret__isnull=True) | Q(secret=user.department)).distinct()
        else:
            events_available = events_available.filter(secret__isnull=True).distinct()

    if f_date:
        events_available = events_available.filter(date__month=1)

    # if f_speakers:
    #     events_available = events_available.filter(speakers__in=f_speakers)
    # if f_speakers:
    #     speakers_query = Q()
    #     for speaker in f_speakers:
    #         speakers_query |= Q(speakers__icontains=speaker)
    #     events_available = events_available.filter(speakers_query)

    tags = [event.tags for event in all_info]

    if f_speakers:
    # Преобразуем имена спикеров в объекты User
        speakers_objects = User.objects.filter(
            Q(first_name__in=[name.split()[0] for name in f_speakers]) &
            Q(last_name__in=[name.split()[1] for name in f_speakers])
        )
        events_available = events_available.filter(speakers__in=speakers_objects)
        
    if f_tags:
        tags_query = Q()
        for tag in f_tags:
            tags_query |= Q(tags__icontains=tag)
        events_available = events_available.filter(tags_query)

    if order_by and order_by != "default":
        events_available = events_available.order_by(order_by)

    if date_start:
        date_start_formatted = datetime.strptime(date_start, '%Y-%m-%d').date()
        events_available = events_available.filter(date__gt=date_start_formatted)

    if date_end:
        date_end_formatted = datetime.strptime(date_end, '%Y-%m-%d').date()
        events_available = events_available.filter(date__lt=date_end_formatted)

    paginator = Paginator(events_available, 3)
    current_page = paginator.page(int(page))

    favorites = Favorite.objects.filter(user=request.user, online__in=current_page)
    favorites_dict = {favorite.online.id: favorite.id for favorite in favorites}

    registered = Registered.objects.filter(user=request.user, online__in=current_page)
    registered_dict = {reg.online.id: reg.id for reg in registered}

    reviews = {}
    for event in current_page:
        content_type = ContentType.objects.get_for_model(event)
        reviews[event.unique_id] = Review.objects.filter(content_type=content_type, object_id=event.id)

    context = {
        'name_page': 'Онлайн',
        'event_card_views': current_page,
        'speakers': speakers,
        'events_admin': events_admin,
        'tags': tags,
        'favorites': favorites_dict,
        'registered': registered_dict,
        'reviews': reviews,
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
    
    favorites = Favorite.objects.filter(user=request.user, online__in=events)
    favorites_dict = {favorite.online.id: favorite.id for favorite in favorites}

    registered = Registered.objects.filter(user=request.user, online__in=events)
    registered_dict = {reg.online.id: reg.id for reg in registered}

    reviews = {}

    for event_rew in events:
        content_type = ContentType.objects.get_for_model(event)
        reviews[event_rew.unique_id] = Review.objects.filter(content_type=content_type, object_id=event.id)

    context = {
        'event': event,
        'reviews': reviews,
        'registered': registered_dict,
        'favorites': favorites_dict, 
    }
    return render(request, 'events_available/card.html', context=context)


@login_required
def offline(request):
    page = request.GET.get('page', 1)
    f_date = request.GET.getlist('f_date', None)
    f_speakers = request.GET.getlist('f_speakers', None)
    f_tags = request.GET.getlist('f_tags', None)
    f_place = request.GET.get('f_place', None)
    order_by = request.GET.get('order_by', None)
    query = request.GET.get('q', None)
    query_name = request.GET.get('qn', None)
    date_start = request.GET.get('date_start', None)
    date_end = request.GET.get('date_end', None)
    user = request.user

    all_info = Events_offline.objects.all()
    # Получаем всех спикеров
    speakers_set = set()
    for event in all_info:
        for speaker in event.speakers.all():
            speakers_set.add(speaker.get_full_name())

    speakers = list(speakers_set)

    for name in speakers:
        names_list = name.split()
        for i in range(0, len(names_list), 3):
            speakers_set.add(' '.join(names_list[i:i+3]))
    
    speakers = list(speakers_set)

    # Получаем всех админов через отношение ManyToMany
    events_admin_set = set()
    for event in all_info:
        for admin in event.events_admin.all():
            events_admin_set.add(admin.get_full_name())

    events_admin = list(events_admin_set)

    if not query_name:
        events_available = Events_offline.objects.order_by('time_start')
    else:
        events_available = q_search_name_offline(query_name)

    if not query:
        events_available = events_available.order_by('time_start')
    else:
        events_available = q_search_offline(query)

    #Фильтрация по скрытым мероприятиям
    if user.is_superuser or user.department.department_name in ['Administration', 'Superuser']:
        pass 
    else:
        if user.department:
            events_available = events_available.filter(Q(secret__isnull=True) | Q(secret=user.department)).distinct()
        else:
            events_available = events_available.filter(secret__isnull=True).distinct()

    if f_date:
        events_available = events_available.filter(date__month=1)

    if date_start:
        date_start_formatted = datetime.strptime(date_start, '%Y-%m-%d').date()
        events_available = events_available.filter(date__gte=date_start_formatted) 

    if date_end:
        date_end_formatted = datetime.strptime(date_end, '%Y-%m-%d').date()
        events_available = events_available.filter(date__lte=date_end_formatted)

    if f_place:
        events_available = events_available.annotate(
            full_place=Concat('town', Value(' '), 'street', Value(' '), 'house', Value(' '), 'cabinet', output_field=CharField())
        ).filter(full_place__icontains=f_place)


    if f_speakers:
        # Преобразуем имена спикеров в объекты User
        speakers_objects = User.objects.filter(
            Q(first_name__in=[name.split()[0] for name in f_speakers]) &
            Q(last_name__in=[name.split()[1] for name in f_speakers])
        )
        events_available = events_available.filter(speakers__in=speakers_objects)
    # if f_speakers:
    #     events_available = events_available.filter(speakers__in=f_speakers)
    # if f_speakers:
    #     speakers_query = Q()
    #     for speaker in f_speakers:
    #         speakers_query |= Q(speakers__icontains=speaker)
    #     events_available = events_available.filter(speakers_query)

    tags = [event.tags for event in all_info]

    if f_tags:
        tags_query = Q()
        for tag in f_tags:
            tags_query |= Q(tags__icontains=tag)
        events_available = events_available.filter(tags_query)

    if order_by and order_by != "default":
        events_available = events_available.order_by(order_by)

    

    paginator = Paginator(events_available, 3)
    current_page = paginator.page(int(page))

    favorites = Favorite.objects.filter(user=request.user, offline__in=current_page)
    favorites_dict = {favorite.offline.id: favorite.id for favorite in favorites}

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
    favorites_dict = {favorite.offline.id: favorite.id for favorite in favorites}
    
    registered = Registered.objects.filter(user=request.user, offline__in=events)
    registered_dict = {reg.offline.id: reg.id for reg in registered}

    context = {
        'event': event,
        'reviews': reviews, 
        'registered': registered_dict,
        'favorites': favorites_dict,
    }

    return render(request, 'events_available/card.html', context=context)

def autocomplete_places(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        query = request.GET.get('term', '')
        places = Events_offline.objects.filter(
            Q(town__icontains=query) | Q(street__icontains=query) | Q(house__icontains=query) | Q(cabinet__icontains=query)
        ).values_list('town', flat=True).distinct()
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

        if model_type == 'offline':
            event = get_object_or_404(Events_offline, id=event_id)
        elif model_type == 'online':
            event = get_object_or_404(Events_online, id=event_id)
        else:
            return JsonResponse({'success': False, 'message': 'Некорректный тип мероприятия'}, status=400)

        content_type = ContentType.objects.get_for_model(event)
        review = Review.objects.create(
            user=request.user,
            content_type=content_type,
            object_id=event.id,
            comment=comment
        )
        return JsonResponse({
            'success': True,
            'message': 'Отзыв добавлен',
            'formatted_date': review.formatted_date()
        })
    return JsonResponse({'success': False, 'message': 'Некорректный запрос'}, status=400)
