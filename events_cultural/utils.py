from events_cultural.models import Attractions, Events_for_visiting
from django.db.models import Q, F, Value
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.contrib.postgres.search import TrigramSimilarity, SearchHeadline
from django.db.models import F, Value
from django.db.models.functions import Greatest
from django.db.models.expressions import Func

def q_search_events_for_visiting(query):
    if query.isdigit() and len(query) <= 5:
        return Events_for_visiting.objects.filter(id=int(query))

    query_ru = SearchQuery(query, config='russian_conf', search_type='websearch')
    query_en = SearchQuery(query, config='english', search_type='websearch')

    vector_ru = SearchVector('name', weight='A', config='russian_conf') + \
                SearchVector('description', weight='B', config='russian_conf')

    vector_en = SearchVector('name', weight='A', config='english') + \
                SearchVector('description', weight='B', config='english')

    result = Events_for_visiting.objects.annotate(
        rank_ru=SearchRank(vector_ru, query_ru),
        rank_en=SearchRank(vector_en, query_en),
        total_rank=Greatest(F('rank_ru'), F('rank_en'))
    ).filter(
        Q(rank_ru__gt=0.0) | Q(rank_en__gt=0.0)
    ).order_by('-total_rank')

    if not result.exists():
        result = Events_for_visiting.objects.annotate(
            similarity=TrigramSimilarity('name', query)
        ).filter(similarity__gt=0.3).order_by('-similarity')

    if not result.exists():
        result = Events_for_visiting.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        ).order_by('-date_add')

    result = result.annotate(
        headline_name=SearchHeadline(
            F('name'),
            query_ru,
            config='russian_conf',
            start_sel='<span style="background-color: #99AABC;">',
            stop_sel='</span>',
            max_fragments=0
        ),
        headline_description=SearchHeadline(
            F('description'),
            query_ru,
            config='russian_conf',
            start_sel='<span style="background-color: #99AABC;">',
            stop_sel='</span>',
            max_fragments=0
        )
    )

    return result
	

	
def q_search_attractions(query):
    if query.isdigit() and len(query) <= 5:
        return Attractions.objects.filter(id=int(query))

    query_ru = SearchQuery(query, config='russian_conf', search_type='websearch')
    query_en = SearchQuery(query, config='english', search_type='websearch')

    vector_ru = SearchVector('name', weight='A', config='russian_conf') + \
                SearchVector('description', weight='B', config='russian_conf')

    vector_en = SearchVector('name', weight='A', config='english') + \
                SearchVector('description', weight='B', config='english')

    result = Attractions.objects.annotate(
        rank_ru=SearchRank(vector_ru, query_ru),
        rank_en=SearchRank(vector_en, query_en),
        total_rank=Greatest(F('rank_ru'), F('rank_en'))
    ).filter(
        Q(rank_ru__gt=0.0) | Q(rank_en__gt=0.0)
    ).order_by('-total_rank')

    if not result.exists():
        result = Attractions.objects.annotate(
            similarity=TrigramSimilarity('name', query)
        ).filter(similarity__gt=0.3).order_by('-similarity')

    if not result.exists():
        result = Attractions.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        ).order_by('-date_add')

    result = result.annotate(
        headline_name=SearchHeadline(
            F('name'),
            query_ru,
            config='russian_conf',
            start_sel='<span style="background-color: #99AABC;">',
            stop_sel='</span>',
            max_fragments=0
        ),
        headline_description=SearchHeadline(
            F('description'),
            query_ru,
            config='russian_conf',
            start_sel='<span style="background-color: #99AABC;">',
            stop_sel='</span>',
            max_fragments=0
        )
    )

    return result