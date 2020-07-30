from django.urls import path
from django.views.generic import TemplateView

app_name = "user"

urlpatterns = [
    path(
        "logged-out", TemplateView.as_view(template_name="user/logged-out.html"), name="logged-out",
    ),
    path(
        "disabled",
        TemplateView.as_view(template_name="user/account-disabled.html"),
        name="disabled",
    ),
]
