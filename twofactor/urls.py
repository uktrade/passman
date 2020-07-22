from django.urls import path

from . import views

app_name = 'twofactor'

urlpatterns = [
    path('enroll/', views.TwoFactorEnrollView.as_view(), name='enroll'),
    path('verify/', views.TwoFactorVerifyView.as_view(), name='verify'),
]
