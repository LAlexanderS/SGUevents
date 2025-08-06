from events_available.models import Events_online, Events_offline
from django.db.models import Q, F, Value
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.contrib.postgres.search import TrigramSimilarity, SearchHeadline
from django.db.models import F, Value
from django.db.models.functions import Greatest
from django.db.models.expressions import Func


from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.db.models import Q, F

from django.contrib.postgres.search import (
    SearchVector, SearchQuery, SearchRank, SearchHeadline, TrigramSimilarity
)
from django.db.models import Q, F, Value, CharField
from django.db.models.functions import Greatest
from django.db.models import Func
import bleach

def q_search_online(query):
    if query.isdigit() and len(query) <= 5:
        return Events_online.objects.filter(id=int(query))

    query_ru = SearchQuery(query, config='russian_conf', search_type='websearch')
    query_en = SearchQuery(query, config='english', search_type='websearch')

    vector_ru = SearchVector('name', weight='A', config='russian_conf') + \
                SearchVector('description', weight='B', config='russian_conf')

    vector_en = SearchVector('name', weight='A', config='english') + \
                SearchVector('description', weight='B', config='english')

    result = Events_online.objects.annotate(
        rank_ru=SearchRank(vector_ru, query_ru),
        rank_en=SearchRank(vector_en, query_en),
        total_rank=Greatest(F('rank_ru'), F('rank_en'))
    ).filter(
        Q(rank_ru__gt=0.0) | Q(rank_en__gt=0.0)
    ).order_by('-total_rank')

    if not result.exists():
        result = Events_online.objects.annotate(
            similarity=TrigramSimilarity('name', query)
        ).filter(similarity__gt=0.3).order_by('-similarity')

    if not result.exists():
        result = Events_online.objects.filter(
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



    
	# keyword = [word for word in query.split() if len(word) > 2]

	# q_objects = Q()
	# for token in keyword:
	# 	q_objects |= Q(description__icontains=token)
	# 	q_objects |= Q(name__icontains=token)


	# return Events_online.objects.filter(q_objects)

	
def q_search_offline(query):
    if query.isdigit() and len(query) <= 5:
        return Events_offline.objects.filter(id=int(query))

    query_ru = SearchQuery(query, config='russian_conf', search_type='websearch')
    query_en = SearchQuery(query, config='english', search_type='websearch')

    vector_ru = SearchVector('name', weight='A', config='russian_conf') + \
                SearchVector('description', weight='B', config='russian_conf')

    vector_en = SearchVector('name', weight='A', config='english') + \
                SearchVector('description', weight='B', config='english')

    result = Events_offline.objects.annotate(
        rank_ru=SearchRank(vector_ru, query_ru),
        rank_en=SearchRank(vector_en, query_en),
        total_rank=Greatest(F('rank_ru'), F('rank_en'))
    ).filter(
        Q(rank_ru__gt=0.0) | Q(rank_en__gt=0.0)
    ).order_by('-total_rank')

    if not result.exists():
        result = Events_offline.objects.annotate(
            similarity=TrigramSimilarity('name', query)
        ).filter(similarity__gt=0.3).order_by('-similarity')

    if not result.exists():
        result = Events_offline.objects.filter(
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

def sanitize_html(text):
    allowed_tags = ['strong', 'em', 'br', 'ul', 'ol', 'li', 'p']
    allowed_attrs = {}
    return bleach.clean(text, tags=allowed_tags, attributes=allowed_attrs, strip=True)