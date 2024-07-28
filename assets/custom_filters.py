from django import template
from django.template.defaultfilters import floatformat

register = template.Library()

@register.filter(name='currency_gbp')
def currency_gbp(value):
    if value is None:
        return "£0.00"
    return f"£{floatformat(value, 2)}"