from axes.decorators import axes_dispatch
from django.urls import path

from localauth import views

urlpatterns = [
    path("login/", axes_dispatch(views.LoginView.as_view()), name="login"),
]
