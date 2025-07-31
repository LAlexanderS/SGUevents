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
from datetime import datetime, time
from users.models import User



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

    filters_applied = False  # По умолчанию считаем, что фильтры не применен

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
    is_logistics = current_user.groups.filter(name="Логистика").exists()

    
    events = sorted(list(chain(online_events, offline_events, attractions, for_visiting)), key=lambda x: x.date_add, reverse=True)

    # Фильтр по названию
    if name_search:
        # Фильтр только по названию
        events = [e for e in events if name_search in e.name ]
        filters_applied = True
    elif query:
        # Полный поиск по названию и описанию через навигационную панель
        # events_available = q_search_online(query)
        # filters_applied = True
        pass
    else:
        # Если ни одного запроса нет, выводим все мероприятия, отсортированные по дате
        pass


    # Фильтр по дате
    if date_start:
        date_start_formatted = datetime.strptime(date_start, '%Y-%m-%d').date()
        events = [e for e in events if e.date and e.date >= date_start_formatted]

    if date_end:
        date_end_formatted = datetime.strptime(date_end, '%Y-%m-%d').date()
        events = [e for e in events if e.date_end and e.date_end <= date_end_formatted]


    # Фильтр по времени 
    if time_to_start:
        time_start_obj = datetime.strptime(time_to_start, '%H:%M').time()
        events = [e for e in events if e.time_start and e.time_start >= time_start_obj]

    if time_to_end:
        time_end_obj = datetime.strptime(time_to_end, '%H:%M').time()
        events = [e for e in events if e.time_end and e.time_end <= time_end_obj]


    # Фильтр по спикерам
    speakers_set = set()
    for event in online_events:
        for speaker in event.speakers.all():
            # Явно формируем строку с Фамилией, Именем и Отчеством
            full_name = f"{speaker.last_name} {speaker.first_name} {speaker.middle_name if speaker.middle_name else ''}".strip()
            speakers_set.add(full_name)

    for event in offline_events:
        for speaker in event.speakers.all():
            # Явно формируем строку с Фамилией, Именем и Отчеством
            full_name = f"{speaker.last_name} {speaker.first_name} {speaker.middle_name if speaker.middle_name else ''}".strip()
            speakers_set.add(full_name)

    speakers = list(speakers_set)
    # Инициализируем пустой список для спикеров, чтобы избежать ошибки, если фильтры по спикерам не применяются
    speakers_objects = []
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
            events = [e for e in events if e.speakers in speakers_objects]
    # Фильтр по тегам

    # Сортировка
    # events.sort(key=lambda e: e.time_start or time.min)


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
        'is_logistics': is_logistics,
        'name_page': "Кабинет администратора",
        'reviews_avg': reviews_avg,
        'speakers': speakers,
        'filters_applied': filters_applied,

    }
    
    return render(request, 'personal/personal.html', context=context)
