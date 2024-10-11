from events_available.models import Events_online, Events_offline
from django.db.models import Q, F, Value
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.contrib.postgres.search import TrigramSimilarity, SearchHeadline
from django.db.models import F, Value
from django.db.models.functions import Greatest
from django.db.models.expressions import Func


from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.db.models import Q, F

def q_search_online(query):
    # Поиск по ID, если запрос состоит только из цифр
    if query.isdigit() and len(query) <= 5:
        return Events_online.objects.filter(id=int(query))

    # Создаем поиск с использованием конфигурации russian_conf
    vector = SearchVector("name", config='russian_conf', weight='A') + SearchVector("description", config='russian_conf', weight='B')
    query_search = SearchQuery(query, config='russian_conf')

    # Выполняем поиск по схожести и релевантности
    result = Events_online.objects.annotate(
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


    
	# keyword = [word for word in query.split() if len(word) > 2]

	# q_objects = Q()
	# for token in keyword:
	# 	q_objects |= Q(description__icontains=token)
	# 	q_objects |= Q(name__icontains=token)


	# return Events_online.objects.filter(q_objects)

	
def q_search_offline(query):
    # Поиск по ID, если запрос состоит только из цифр
    if query.isdigit() and len(query) <= 5:
        return Events_offline.objects.filter(id=int(query))

    # Создаем поиск с использованием конфигурации russian_conf
    vector = SearchVector("name", config='russian_conf', weight='A') + SearchVector("description", config='russian_conf', weight='B')
    query_search = SearchQuery(query, config='russian_conf')

    # Выполняем поиск по схожести и релевантности
    result = Events_offline.objects.annotate(
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

def q_search_name_offline(query_name):
    if query_name.isdigit() and len(query_name) <= 5:
        return Events_offline.objects.filter(id=int(query_name))
    
    vector = SearchVector("name")
    query_search = SearchQuery(query_name)
    
    result = Events_offline.objects.annotate(rank=SearchRank(vector, query_search)).filter(rank__gt=0).order_by("-rank")
    
    result = result.annotate(
        headline=SearchHeadline(
            "name",
            query_search,
            start_sel='<span style="background-color: yellow;">',
            stop_sel="</span>",
        )
    )
    
    return result