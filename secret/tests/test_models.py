import pytest

from user.tests.factories import UserFactory
from secret.tests.factories import SecretFactory

pytestmark = pytest.mark.django_db


class TestModelPermissions:
    def test_superuer_can_view_instance(self):
        user = UserFactory(is_superuser=True)

        secret = SecretFactory()

        assert user.has_perm("secret.view_secret", secret)

        assert user.has_perm("secret.change_secret", secret)
