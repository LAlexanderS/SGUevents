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
from django.db.models import Q

@login_required
def attractions(request):
    page = request.GET.get('page', 1)
    f_attractions = request.GET.get('f_attractions', None)
    order_by = request.GET.get('order_by', None)
    query = request.GET.get('q', None)
    user = request.user
    f_tags = request.GET.getlist('f_tags', None)
    
    all_info = Attractions.objects.all()
    # Получаем всех админов через отношение ManyToMany
    events_admin_set = set()
    for event in all_info:
        for admin in event.events_admin.all():
            events_admin_set.add(admin.get_full_name())

    events_admin = list(events_admin_set)

    if not query:
        events_cultural = Attractions.objects.order_by('time_start')
    else:
        events_cultural = q_search_attractions(query)

    #Фильтрация по скрытым мероприятиям
    if user.is_superuser or user.department.department_name in ['Administration', 'Superuser']:
        pass 
    else:
        if user.department:
            events_cultural = events_cultural.filter(Q(secret__isnull=True) | Q(secret=user.department)).distinct()
        else:
            events_cultural = events_cultural.filter(secret__isnull=True).distinct()

    tags = [event.tags for event in all_info]
     
    if f_tags:
        tags_query = Q()
        for tag in f_tags:
            tags_query |= Q(tags__icontains=tag)
        events_cultural = events_cultural.filter(tags_query)
    
    if order_by and order_by != "default":
        events_cultural = events_cultural.order_by(order_by)

    paginator = Paginator(events_cultural, 3)
    current_page = paginator.page(int(page))

    favorites = Favorite.objects.filter(user=request.user, attractions__in=current_page)
    favorites_dict = {favorite.attractions.id: favorite.id for favorite in favorites}

    events = Attractions.objects.all()
    
    reviews = {}
    for event in events:
        content_type = ContentType.objects.get_for_model(event)
        reviews[event.unique_id] = Review.objects.filter(content_type=content_type, object_id=event.id)

    context = {
        'name_page': 'Достопримечательности',
        'event_card_views': current_page,
        'favorites': favorites_dict,
        'reviews': reviews, 
        'events_admin': events_admin,
        'tags': list(set(tag for event in all_info if event.tags for tag in event.tags.split(','))),

        'f_tags': f_tags,
        

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
    favorites_dict = {favorite.attractions.id: favorite.id for favorite in favorites}
    
    reviews = {}

    for event_rew in events:
        content_type = ContentType.objects.get_for_model(event)
        reviews[event_rew.unique_id] = Review.objects.filter(content_type=content_type, object_id=event.id)

    context = {
        'event': event,
        'reviews': reviews, 
        'favorites': favorites_dict,
    }
    return render(request, 'events_cultural/card.html', context=context)

@login_required
def events_for_visiting(request):
    page = request.GET.get('page', 1)
    f_events_for_visiting = request.GET.get('f_events_for_visiting', None)
    order_by = request.GET.get('order_by', None)
    query = request.GET.get('q', None)
    user = request.user
    f_tags = request.GET.getlist('f_tags', None)


    all_info = Events_for_visiting.objects.all()
    # Получаем всех админов через отношение ManyToMany
    events_admin_set = set()
    for event in all_info:
        for admin in event.events_admin.all():
            events_admin_set.add(admin.get_full_name())

    events_admin = list(events_admin_set)

    if not query:
        events_cultural = Events_for_visiting.objects.order_by('time_start')
    else:
        events_cultural = q_search_events_for_visiting(query)
    
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

    tags = [event.tags for event in all_info]
     
    if f_tags:
        tags_query = Q()
        for tag in f_tags:
            tags_query |= Q(tags__icontains=tag)
        events_cultural = events_cultural.filter(tags_query)

    paginator = Paginator(events_cultural, 3)
    current_page = paginator.page(int(page))

    favorites = Favorite.objects.filter(user=request.user, for_visiting__in=current_page)
    favorites_dict = {favorite.for_visiting.id: favorite.id for favorite in favorites}

    registered = Registered.objects.filter(user=request.user, for_visiting__in=current_page)
    registered_dict = {reg.for_visiting.id: reg.id for reg in registered}

    reviews = {}
    for event in current_page:
        content_type = ContentType.objects.get_for_model(event)
        reviews[event.unique_id] = Review.objects.filter(content_type=content_type, object_id=event.id)

    context = {
        'name_page': 'Доступные к посещению',
        'event_card_views': current_page,
        'favorites': favorites_dict,
        'registered': registered_dict,
        'reviews': reviews,
        'events_admin': events_admin,
        'tags': list(set(tag for event in all_info if event.tags for tag in event.tags.split(','))),
        
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
    favorites_dict = {favorite.for_visiting.id: favorite.id for favorite in favorites}

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
        

    }
    return render(request, 'events_cultural/card.html', context=context)

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
        return JsonResponse({
            'success': True,
            'message': 'Отзыв добавлен',
            'formatted_date': review.formatted_date()
        })
    return JsonResponse({'success': False, 'message': 'Некорректный запрос'}, status=400)

@login_required
def index(request):
    return render(request, 'events_cultural/index.html')
