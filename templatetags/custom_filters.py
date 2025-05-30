from django import template
from collections import defaultdict

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, [])