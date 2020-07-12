from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import include, path

from core.views import admin_login_view

urlpatterns = [
    path('admin/login/', admin_login_view, name='admin-login-override'),
    path('admin/', admin.site.urls),
    path('auth/', include('authbroker_client.urls', namespace='authbroker_client')),
    path('logout/', LogoutView.as_view(), name='logout'),

    path('user/', include('user.urls', namespace='user')),
    path('', include('secret.urls', namespace='secret')),
]
