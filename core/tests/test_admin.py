import pytest

from django.urls import reverse

from django_otp import DEVICE_ID_SESSION_KEY

from user.tests.factories import UserFactory


pytestmark = pytest.mark.django_db


def otp_verify_user(user, client):
    session = client.session
    session[DEVICE_ID_SESSION_KEY] = user.totpdevice_set.first().persistent_id
    session.save()


def test_unauthenticated_user_is_redirected_to_sso(client):
    response = client.get(reverse("admin:index"))

    assert response.status_code == 302
    assert response.url == reverse("authbroker_client:login")


def test_authenticated_but_unverified_user_is_redirected_to_login(client):
    user = UserFactory(is_active=True, is_staff=True, two_factor_enabled=True)
    client.force_login(user)

    response = client.get(reverse("admin:index"))

    assert response.status_code == 302
    assert response.url.startswith(reverse("admin:login"))


def test_unverified_user_on_login_is_redirected_to_otp_verify(client):
    user = UserFactory(is_active=True, is_staff=True, two_factor_enabled=True)
    client.force_login(user)

    response = client.get(reverse("admin:login"))

    assert response.status_code == 302
    assert response.url == reverse("twofactor:verify")


def test_authenticated_and_verified_user_can_access_admin(client):
    user = UserFactory(is_active=True, is_staff=True, two_factor_enabled=True)
    otp_verify_user(user, client)
    client.force_login(user)

    response = client.get(reverse("admin:login"))

    assert response.status_code == 302
    assert response.url == reverse("admin:index")
