from django.urls import path

from . import views

app_name = 'secret'

urlpatterns = [
    path('', views.SecretListView.as_view(), name='list'),
    path('<str:pk>', views.SecretDetailView.as_view(), name='detail'),
    path('create/', views.SecretCreateView.as_view(), name='create'),
]
