from django import template
from scheduler.models import Lesson

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def range_filter(value, arg):
    start, end = map(int, arg.split(","))
    return range(start, end + 1)

@register.filter
def session_name(session):
    return dict(Lesson.SESSION).get(session)