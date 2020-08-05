import pytest

from django.urls import reverse

from secret.tests.factories import SecretFactory
from user.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestListView:
    def test_auth_required(self, client):
        response = client.get(reverse("secret:list"))

        assert response.status_code == 302
        assert response.url == reverse("authbroker_client:login")

    def test_verification_not_required(self, client):
        user = UserFactory(is_active=True, two_factor_enabled=True)

        client.force_login(user)

        response = client.get(reverse("secret:list"))

        assert response.status_code == 200

    def test_nav_groups_match_users_groups(self):
        pass

    def test_superuser_sees_all_groups(self):
        pass

    def test_user_can_only_filter_on_assigned_groups(self):
        pass

    def test_search_term_returns_only_permitted_results(self):
        pass

    def test_filter_results(self):
        pass

    def test_search(self):
        pass

    def test_pagination(self):
        pass


class TestUpdateView:
    def test_auth_required(self, client):
        secret = SecretFactory()
        response = client.get(reverse("secret:detail", kwargs={"pk": secret.pk}))

        assert response.status_code == 302
        assert response.url == reverse("authbroker_client:login")

    def owner_groups_list_is_restricted(self):
        pass

    def test_user_requires_owner_group_to_update_entry(self):
        pass

    def test_user_cannot_manipulate_owner_group(self):
        pass

    def test_success(self):
        pass

    def test_view_audit_entry(self):
        pass

    def test_update_audit_entry(self):
        pass


class TestCreateVew:
    def test_auth_required(self, client):
        response = client.get(reverse("secret:create"))

        assert response.status_code == 302
        assert response.url == reverse("authbroker_client:login")

    def test_verification_rerequired(self):
        pass

    def test_page_load(self):
        pass

    def test_redirects_to_update_view_on_success(self):
        pass

    def test_user_cannot_manipulate_owner_group(self):
        pass

    def test_create_audit_entry(self):
        pass

    def test_success(self):
        pass
