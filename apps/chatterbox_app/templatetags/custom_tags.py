from django import template

register = template.Library()

@register.filter(name='proper_case')
def proper_case(value):
    return value.title()