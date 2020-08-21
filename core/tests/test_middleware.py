import pytest

from django.urls import reverse

from user.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_user_without_2fa_is_redirected_to_enrollment_page(client):
    user = UserFactory(is_active=True, two_factor_enabled=False)

    client.force_login(user)

    response = client.get(reverse("secret:list"))

    assert response.status_code == 302
    assert response.url == reverse("twofactor:enroll")


def test_user_disabled(client):
    user = UserFactory(is_active=False, two_factor_enabled=True)

    client.force_login(user, backend="core.backends.CustomAuthbrokerBackend")

    response = client.get(reverse("secret:list"))

    assert response.status_code == 302
    assert response.url == reverse("user:disabled")
