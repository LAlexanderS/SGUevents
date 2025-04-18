from itertools import chain
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank, SearchHeadline, TrigramSimilarity
from django.db.models import Q, F, Value
from django.db.models.functions import Greatest
from django.db.models import CharField
from events_available.models import Events_online, Events_offline
from events_cultural.models import Attractions, Events_for_visiting


def q_search_all(query):
    if query.isdigit() and len(query) <= 5:
        return list(chain(
            Events_online.objects.filter(id=int(query)),
            Events_offline.objects.filter(id=int(query)),
            Attractions.objects.filter(id=int(query)),
            Events_for_visiting.objects.filter(id=int(query))
        ))

    query_ru = SearchQuery(query, config='russian_conf', search_type='websearch')
    query_en = SearchQuery(query, config='english', search_type='websearch')

    def annotate_model(model, name):
        vector_ru = SearchVector('name', weight='A', config='russian_conf') + \
                    SearchVector('description', weight='B', config='russian_conf')
        vector_en = SearchVector('name', weight='A', config='english') + \
                    SearchVector('description', weight='B', config='english')

        result = model.objects.annotate(
            rank_ru=SearchRank(vector_ru, query_ru),
            rank_en=SearchRank(vector_en, query_en),
            total_rank=Greatest(F('rank_ru'), F('rank_en'))
        ).filter(
            Q(rank_ru__gt=0.0) | Q(rank_en__gt=0.0)
        ).order_by('-total_rank')

        if not result.exists():
            result = model.objects.annotate(
                similarity=TrigramSimilarity('name', query)
            ).filter(similarity__gt=0.3).order_by('-similarity')

        if not result.exists():
            result = model.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            ).order_by('-date_add')

        return result.annotate(
            headline_name=SearchHeadline(
                F('name'), query_ru,
                config='russian_conf',
                start_sel='<span style="background-color: #99AABC;">',
                stop_sel='</span>'
            ),
            headline_description=SearchHeadline(
                F('description'), query_ru,
                config='russian_conf',
                start_sel='<span style="background-color: #99AABC;">',
                stop_sel='</span>'
            )
        )

    online_results = annotate_model(Events_online, 'online')
    offline_results = annotate_model(Events_offline, 'offline')
    attractions_results = annotate_model(Attractions, 'attractions')
    for_visiting_results = annotate_model(Events_for_visiting, 'for_visiting')

    return list(chain(online_results, offline_results, attractions_results, for_visiting_results))
