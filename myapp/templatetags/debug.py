from django import template

register = template.Library()

@register.filter
def pprint(value):
    """Print a variable in a readable format."""
    import pprint
    return pprint.pformat(value) 