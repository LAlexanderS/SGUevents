from itertools import chain
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from events_available.models import Events_online, Events_offline
from events_cultural.models import Attractions, Events_for_visiting
from django.contrib.auth.models import Group
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage, PageNotAnInteger
from django.contrib.contenttypes.models import ContentType
from bookmarks.models import Review
from django.db.models import Avg


# @login_required
# def add_online_event(request):
#     if request.method == 'POST':
#         form = EventsOnlineForm(request.POST, request.FILES)
#         if form.is_valid():
#             form.save()
#             return redirect(reverse('personal:personal'))
#     else:
#         form = EventsOnlineForm()

#     form_html = render_to_string('personal/event_form.html', {'form': form})
#     return JsonResponse({'form_html': form_html})

# @login_required
# def add_offline_event(request):
#     if request.method == 'POST':
#         form = EventsOfflineForm(request.POST, request.FILES)
#         if form.is_valid():
#             form.save()
#             return redirect(reverse('personal:personal'))
#     else:
#         form = EventsOfflineForm()

#     form_html = render_to_string('personal/event_form.html', {'form': form})
#     return JsonResponse({'form_html': form_html})

@login_required
def personal(request):
    page = request.GET.get('page', 1)
    current_user = request.user
    if current_user.is_staff:
        online_events = Events_online.objects.filter(events_admin=current_user.pk)
        offline_events = Events_offline.objects.filter(events_admin=current_user.pk)
        attractions = Attractions.objects.filter(events_admin=current_user.pk)
        for_visiting = Events_for_visiting.objects.filter(events_admin=current_user.pk)
    else:
        online_events = []
        offline_events = []
        attractions = []
        for_visiting = []

    is_online_group = current_user.groups.filter(name="Онлайн мероприятия").exists()
    is_offline_group = current_user.groups.filter(name="Оффлайн мероприятия").exists()
    is_attraction_group = current_user.groups.filter(name="Достопримечательности").exists()
    is_for_visiting_group = current_user.groups.filter(name="Доступные к посещению").exists()
    
    events = list(chain(online_events, offline_events, attractions, for_visiting))

    paginator = Paginator(events, 10)
    try:
        current_page = paginator.page(int(page))
    except PageNotAnInteger:
        # Если страница не является целым числом, возвращаем первую страницу
        current_page = paginator.page(1)
    except EmptyPage:
        # Если страница пуста (например, второй страницы не существует), возвращаем последнюю страницу
        current_page = paginator.page(paginator.num_pages)

    reviews_avg = {}
    for event in events:
        content_type = ContentType.objects.get_for_model(event)
        avg_rating = Review.objects.filter(
            content_type=content_type,
            object_id=event.id,
            rating__isnull=False
        ).aggregate(Avg('rating'))['rating__avg']
        reviews_avg[event.id] = round(avg_rating, 1) if avg_rating else 0

    context = {
        'event_card_views': current_page,
        'online_events': online_events,
        'offline_events': offline_events,
        'is_online_group': is_online_group,
        'is_offline_group': is_offline_group,
        'is_attraction_group': is_attraction_group,
        'is_for_visiting_group': is_for_visiting_group,
        'name_page': "Кабинет администратора",
        'reviews_avg': reviews_avg,
    }
    
    return render(request, 'personal/personal.html', context)
