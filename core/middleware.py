from django.conf import settings
from django.shortcuts import redirect
from django.urls import resolve, reverse

from django_otp import user_has_device


class ProtectAllViewsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        public_views = getattr(settings, "PUBLIC_VIEWS", [])
        require_2fa = getattr(settings, "REQUIRE_2FA", True)

        if not request.user.is_authenticated:
            # user must sign in
            if (
                resolve(request.path).app_name != "authbroker_client"
                and request.path not in public_views
            ):
                return redirect("authbroker_client:login")
        else:
            # user is not enrolled for 2fa
            if (
                require_2fa
                and not user_has_device(request.user)
                and request.path != reverse("twofactor:enroll")
            ):
                return redirect("twofactor:enroll")

        response = self.get_response(request)

        return response
