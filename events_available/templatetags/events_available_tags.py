from django import template
from django.utils.http import urlencode
from events_available.models import Events_offline, Events_online

register = template.Library()

@register.simple_tag()
def tag_online():
    return Events_online.objects.all()

@register.simple_tag()
def tag_offline():
    return Events_offline.objects.all()

@register.simple_tag(takes_context=True)
def change_params(context, **kwargs):
    query = context['request'].GET.dict()
    for key, value in kwargs.items():
        if value in [None, '']:
            query.pop(key, None)
        else:
            query[key] = value
    return urlencode(query)

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

