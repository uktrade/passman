from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse


def admin_login_view(request):
    """A replacement admin login view that will direct the user through the SSO
    authentication flow. """

    next_url = request.GET.get(
        'next',
        reverse('admin:index')
    )

    if request.user.is_authenticated:
        if (request.user.is_staff or request.user.is_superuser) and request.user.is_active:
            return redirect(next_url)
        else:
            raise PermissionDenied

    return redirect('%s?next=%s' % (reverse(settings.LOGIN_URL), next_url))
