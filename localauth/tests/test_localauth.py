import pytest

from django.urls import reverse
from user.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    user = UserFactory(email="user1@example.com")

    user.set_password("letmein123")
    user.save()

    return user


class TestLogin:
    def test_user_incorrect_password(self, client, user):

        response = client.post(
            reverse("localauth:login"), {"username": user.email, "password": "letmein2017"}
        )

        assert response.status_code == 200 
        assert "Your username and password didn\\\'t match. Please try again." in str(response.content)

    def test_user_can_authenticate(self, client, user):

        response = client.post(
            reverse("localauth:login"), {"username": user.email, "password": "letmein123"}
        )

        assert response.status_code == 302
        assert response.url == '/'
