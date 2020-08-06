import pytest

from guardian.shortcuts import assign_perm

from secret.filters import SecretFilter
from secret.models import Secret
from user.tests.factories import UserFactory, GroupFactory
from .factories import SecretFactory

pytestmark = pytest.mark.django_db


class TestSecretFilter:
    def test_group_filter_for_group_not_assigned_to_user(self, rf):
        user = UserFactory()
        group = GroupFactory()
        secret = SecretFactory()

        assign_perm("view_secret", group, secret)

        request = rf.get("/some/url")
        request.user = user

        filter = SecretFilter(
            request=request, queryset=Secret.objects.all(), data={"group": group.name},
        )

        assert not filter.qs

    def test_filter_on_group(self, rf):
        user = UserFactory()
        group = GroupFactory()
        secret = SecretFactory()

        assign_perm("view_secret", group, secret)

        request = rf.get("/some/url")
        request.user = user

        filter = SecretFilter(
            request=request, queryset=Secret.objects.all(), data={"group": group.name},
        )

        assert not filter.qs

    def test_search_filter(self, rf):
        user = UserFactory()
        secret1 = SecretFactory(name="aws-1")
        SecretFactory(name="aws-2")

        assign_perm("view_secret", user, secret1)

        request = rf.get("/some/url")
        request.user = user

        filter = SecretFilter(request=request, queryset=Secret.objects.all(), data={"name": "aws"},)

        assert filter.qs.count() == 1
        assert filter.qs.first() == secret1

    def test_user_gets_results_with_change_permission(self, rf):
        user = UserFactory()
        secret = SecretFactory(name="aws-1")

        assign_perm("change_secret", user, secret)

        request = rf.get("/some/url")
        request.user = user

        filter = SecretFilter(request=request, queryset=Secret.objects.all())

        assert filter.qs.count() == 1

    def test_filter_on_my_secrets(self, rf):
        """We expect to see secrets assigned directly to the user, not assigned to
        a group"""
        group = GroupFactory()
        user = UserFactory()
        user.groups.add(group)
        secret1 = SecretFactory(name="aws-1")
        secret2 = SecretFactory(name="aws-1")

        assign_perm("view_secret", user, secret1)
        assign_perm("view_secret", group, secret2)

        request = rf.get("/some/url")
        request.user = user

        filter = SecretFilter(request=request, queryset=Secret.objects.all(), data={"me": True})

        assert filter.qs.count() == 1
        assert filter.qs.first() == secret1

    def test_no_perms_no_results(self, rf):
        """If you have no permission you should see no results"""
        user = UserFactory()
        SecretFactory(name="aws-1")

        request = rf.get("/some/url")
        request.user = user

        filter = SecretFilter(request=request, queryset=Secret.objects.all())

        assert filter.qs.count() == 0

    def test_superuser_gets_all_data(self, rf):
        user = UserFactory(is_superuser=True)
        SecretFactory.create_batch(5)

        request = rf.get("/some/url")
        request.user = user

        filter = SecretFilter(request=request, queryset=Secret.objects.all())

        assert filter.qs.count() == 5
