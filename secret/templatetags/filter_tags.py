from urllib.parse import urlencode

from django import template

register = template.Library()


FILTER_PARAM = "o"


@register.simple_tag(takes_context=True)
def filter_ordering_qs(context, field_name):
    request = context["request"]
    qs_params = {name: value for name, value in request.GET.items()}

    filter = qs_params.get(FILTER_PARAM, "")

    if filter != field_name:
        filter = field_name
    else:
        filter = f"-{field_name}"

    qs_params[FILTER_PARAM] = filter

    return "?" + urlencode(qs_params)
