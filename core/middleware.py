from django.conf import settings
from django.shortcuts import redirect
from django.urls import resolve, reverse

from django_otp import user_has_device


from django.contrib.auth import REDIRECT_FIELD_NAME
from urllib.parse import urlparse, urlencode


class ProtectAllViewsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def get_auth_redirect_url(self, request):

        next_url = urlencode(
            {
                REDIRECT_FIELD_NAME: request.path,
            }
        )

        redirect_url = reverse("authbroker_client:login")

        return redirect(f"{redirect_url}?{next_url}")

    def __call__(self, request):
        public_views = getattr(settings, "PUBLIC_VIEWS", [])
        require_2fa = getattr(settings, "REQUIRE_2FA", True)

        if not request.user.is_authenticated:
            # user must sign in
            if (
                resolve(request.path).app_name != "authbroker_client"
                and request.path not in public_views
            ):
                return self.get_auth_redirect_url(request)
        else:
            # user is not enrolled for 2fa
            if (
                require_2fa
                and not user_has_device(request.user)
                and request.path != reverse("twofactor:enroll")
            ):
                return redirect("twofactor:enroll")
            if not request.user.is_active and request.path != reverse("user:disabled"):
                return redirect("user:disabled")

        response = self.get_response(request)

        return response
