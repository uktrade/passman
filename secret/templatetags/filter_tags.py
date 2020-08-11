from urllib.parse import urlencode

from django import template

register = template.Library()


FILTER_PARAM = "o"


VALID_QS_PARAMS = ["group", "name", "page", "me", "o"]


def extact_qs_params(request):
    return {name: value for name, value in request.GET.items() if name in VALID_QS_PARAMS}


@register.simple_tag(takes_context=True)
def filter_querystring(context, field_name):
    request = context["request"]
    qs_params = extact_qs_params(request)

    filter = qs_params.get(FILTER_PARAM, "")

    if filter != field_name:
        filter = field_name
    else:
        filter = f"-{field_name}"

    qs_params[FILTER_PARAM] = filter

    return "?" + urlencode(qs_params)


@register.simple_tag(takes_context=True)
def page_querystring(context, page_number):
    request = context["request"]
    qs_params = extact_qs_params(request)

    qs_params["page"] = str(page_number)

    return "?" + urlencode(qs_params)
