from django import template

register = template.Library()

@register.filter
def get_image_url(field):
    if not field:
        return ""
    try:
        print(field)
        url = field.url
        if url.startswith("/media"):
            return url
        else:
            return field
    except AttributeError:
        # If field is a string, check if it starts with /media
        if isinstance(field, str) and field.startswith("/media"):
            return field
        return field
