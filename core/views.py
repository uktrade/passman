from django.contrib.auth import REDIRECT_FIELD_NAME
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme


def get_redirect_url(request):
    """Return the user-originating redirect URL if it's safe."""
    redirect_to = request.POST.get(REDIRECT_FIELD_NAME, request.GET.get(REDIRECT_FIELD_NAME, ""))
    url_is_safe = url_has_allowed_host_and_scheme(
        url=redirect_to, allowed_hosts=request.get_host(), require_https=request.is_secure(),
    )
    return redirect_to if url_is_safe else ""


def admin_login_view(request):
    """A replacement admin login view that will direct the user through the SSO
    authentication flow. """

    next_url = get_redirect_url(request) or reverse("admin:index")

    if request.user.is_authenticated:
        if (request.user.is_staff or request.user.is_superuser) and request.user.is_active:
            if not request.user.is_verified():
                return redirect("twofactor:verify")
            return redirect(next_url)
        else:
            raise PermissionDenied

    return redirect("%s?next=%s" % (reverse(settings.LOGIN_URL), next_url))
