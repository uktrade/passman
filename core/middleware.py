import logging

from django.conf import settings
from django.shortcuts import redirect
from django.urls import resolve, reverse

from django_otp import user_has_device


SECURITY_LOGGER_NAME = "security.audit"


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


class AccessLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger(SECURITY_LOGGER_NAME)

    def __call__(self, request):

        self.logger.info({"path": request.path, "user": request.user})

        response = self.get_response(request)

        self.logger.info({"status_code": response.status_code, "user": request.user})

        return response
