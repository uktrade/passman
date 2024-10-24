from axes.decorators import axes_dispatch
from django.conf import settings
from django.contrib.auth import views
from django.shortcuts import Http404
from django.utils.decorators import method_decorator


class FeatureFlaggedMixin:
    def dispatch(self, *args, **kwargs):
        if not settings.LOCAL_AUTH_PAGE:
            raise Http404()
        return super().dispatch(*args, **kwargs)


@method_decorator(axes_dispatch, name="dispatch")
class LoginView(FeatureFlaggedMixin, views.LoginView):
    pass
