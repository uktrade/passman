import pytest


class TestListView:
    def test_auth_required(self):
        pass

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
    def test_user_cannot_manipulate_owner_group(self):
        pass

    def test_create_audit_entry(self):
        pass

    def test_success(self):
        pass
