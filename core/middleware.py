from django.conf import settings
from django.shortcuts import redirect
from django.urls import resolve, reverse


class ProtectAllViewsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if resolve(request.path).app_name != 'authbroker_client' and \
                not request.user.is_authenticated and request.path not in getattr(settings, 'PUBLIC_VIEWS', []):
            return redirect('authbroker_client:login')

        if request.user.is_authenticated and not request.user.is_active and request.path != reverse('user:disabled'):
            return redirect('user:disabled')

        response = self.get_response(request)

        return response
