import pytest

from user.tests.factories import UserFactory
from secret.tests.factories import SecretFactory

from guardian.shortcuts import assign_perm, get_perms

pytestmark = pytest.mark.django_db


class TestModelPermissions:
    def test_superuer_can_view_instance(self):
        user = UserFactory(is_superuser=True)

        secret = SecretFactory()

        assert user.has_perm("secret.view_secret", secret)

        assert user.has_perm("secret.change_secret", secret)

    @pytest.mark.parametrize(
        "start_permissions, input, expected",
        [
            ([], "view_secret", {"view_secret"}),
            ([], "change_secret", {"view_secret", "change_secret"}),
            (["view_secret"], "view_secret", {"view_secret"}),
            (["change_secret"], "view_secret", {"view_secret"}),
            (["change_secret"], "change_secret", {"view_secret", "change_secret"}),
            (["change_secret", "view_secret"], "view_secret", {"view_secret"}),
            (["change_secret", "view_secret"], "change_secret", {"change_secret", "view_secret"}),
        ],
    )
    def test_permission(self, start_permissions, input, expected):
        secret = SecretFactory()
        user = UserFactory()

        for perm in start_permissions:
            assign_perm(perm, user, secret)

        secret.set_permission(user, input)

        assert set(get_perms(user, secret)) == expected

    @pytest.mark.parametrize(
        "start_permissions",
        [["view_secret"], ["change_secret"], ["view_secret", "change_secret"], [],],
    )
    def test_remove_permissions(self, start_permissions):
        secret = SecretFactory()
        user = UserFactory()

        for perm in start_permissions:
            assign_perm(perm, user, secret)

        secret.remove_permissions(user)

        assert get_perms(user, secret) == []
