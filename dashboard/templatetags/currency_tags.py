from django import template

register = template.Library()

@register.filter(name='money_format')
def money_format(value):
    try:
        if value is None:
            return "0"
        # Ensure it's a number and format with spaces
        return "{:,}".format(int(value)).replace(",", " ")
    except (ValueError, TypeError):
        return value
