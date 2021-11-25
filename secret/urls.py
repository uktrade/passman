from django.urls import path

from . import views

app_name = "secret"

urlpatterns = [
    path("", views.SecretListView.as_view(), name="list"),
    path("secret/<str:pk>/", views.SecretDetailView.as_view(), name="detail"),
    path("secret/<str:pk>/delete/", views.SecretDeleteView.as_view(), name="delete"),
    path(
        "secret/<str:pk>/mfa/setup/",
        views.SecretMFASetupView.as_view(),
        name="mfa_setup",
    ),
    path(
        "secret/<str:pk>/mfa/delete/",
        views.SecretMFADeleteView.as_view(),
        name="mfa_delete",
    ),
    path(
        "secret/<str:pk>/mfa/",
        views.SecretMFAView.as_view(),
        name="mfa",
    ),
    path("secret/<str:pk>/audit/", views.SecretAuditView.as_view(), name="audit"),
    path(
        "secret/<str:pk>/sharing/",
        views.SecretPermissionsView.as_view(),
        name="permissions",
    ),
    path(
        "secret/<str:pk>/sharing/delete/",
        views.SecretPermissionsDeleteView.as_view(),
        name="delete-permission",
    ),
    path("create/", views.SecretCreateView.as_view(), name="create"),
]
