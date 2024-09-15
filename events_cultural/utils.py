from events_cultural.models import Attractions, Events_for_visiting
from django.db.models import Q
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector, SearchHeadline

def q_search_events_for_visiting(query):
	# Поиск по ID, если запрос состоит только из цифр
    if query.isdigit() and len(query) <= 5:
        return Events_for_visiting.objects.filter(id=int(query))

    # Создаем поиск с использованием конфигурации russian_conf
    vector = SearchVector("name", config='russian_conf', weight='A') + SearchVector("description", config='russian_conf', weight='B')
    query_search = SearchQuery(query, config='russian_conf')

    # Выполняем поиск по схожести и релевантности
    result = Events_for_visiting.objects.annotate(
        rank=SearchRank(vector, query_search)  # Оценка релевантности
    ).filter(
        rank__gt=0  # Отфильтровываем результаты с релевантностью больше 0
    ).order_by('-rank')  # Сортировка по релевантности

    # Добавляем подсветку найденных ключевых слов
    result = result.annotate(
        headline_name=SearchHeadline(
            "name",
            query_search,
            config="russian_conf",  # Используем нашу конфигурацию
            start_sel='<span style="background-color: yellow;">',
            stop_sel="</span>",
        ),
        headline_description=SearchHeadline(
            "description",
            query_search,
            config="russian_conf",  # Используем нашу конфигурацию
            start_sel='<span style="background-color: yellow;">',
            stop_sel="</span>",
        )
    )

    return result
	

	
def q_search_attractions(query):
	# Поиск по ID, если запрос состоит только из цифр
    if query.isdigit() and len(query) <= 5:
        return Attractions.objects.filter(id=int(query))

    # Создаем поиск с использованием конфигурации russian_conf
    vector = SearchVector("name", config='russian_conf', weight='A') + SearchVector("description", config='russian_conf', weight='B')
    query_search = SearchQuery(query, config='russian_conf')

    # Выполняем поиск по схожести и релевантности
    result = Attractions.objects.annotate(
        rank=SearchRank(vector, query_search)  # Оценка релевантности
    ).filter(
        rank__gt=0  # Отфильтровываем результаты с релевантностью больше 0
    ).order_by('-rank')  # Сортировка по релевантности

    # Добавляем подсветку найденных ключевых слов
    result = result.annotate(
        headline_name=SearchHeadline(
            "name",
            query_search,
            config="russian_conf",  # Используем нашу конфигурацию
            start_sel='<span style="background-color: yellow;">',
            stop_sel="</span>",
        ),
        headline_description=SearchHeadline(
            "description",
            query_search,
            config="russian_conf",  # Используем нашу конфигурацию
            start_sel='<span style="background-color: yellow;">',
            stop_sel="</span>",
        )
    )

    return result
	