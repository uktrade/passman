import pytest

from .factories import GroupFactory, UserFactory
from user.models import User

pytestmark = pytest.mark.django_db


class TestModel:
    def test_permitted_groups_with_superuser(self):
        GroupFactory.create_batch(5)

        user = UserFactory(is_superuser=True, create_groups=["a", "b", "c", "d", "e"])

        result = user.get_permitted_groups()

        assert result.count() == 10

    def test_permitted_groups(self):
        GroupFactory.create_batch(5)

        user_groups = ["a", "b", "c", "d", "e"]

        user = UserFactory(is_superuser=False, create_groups=user_groups)

        result = user.get_permitted_groups()

        assert set([group.name for group in result]) == set(user_groups)

        assert result.count() == 5


class TestModelManager:
    def test_create_superuser(self):
        user = User.objects.create_superuser("test@test.com", "some password")

        assert user.is_active
        assert user.is_superuser
        assert not user.has_usable_password()
