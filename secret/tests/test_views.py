import pytest
import re
from urllib.parse import quote_plus

from django.urls import reverse
from django.utils import timezone

from guardian.shortcuts import assign_perm, get_perms

from audit.models import Actions, Audit
from secret.models import Secret
from secret.tests.factories import SecretFactory
from user.tests.factories import UserFactory, otp_verify_user, GroupFactory

pytestmark = pytest.mark.django_db


def login_and_verify_user(client, verify=True, **extra_user_args):
    user = UserFactory(two_factor_enabled=True, **extra_user_args)

    client.force_login(user)

    if verify:
        otp_verify_user(user, client)

    return user


class TestListView:
    def test_auth_required(self, client):
        url = reverse("secret:list")
        response = client.get(url)

        assert response.status_code == 302

        qs = "?next=" + quote_plus(url)
        assert response.url == reverse("authbroker_client:login") + qs

    def test_verification_not_required(self, client):
        login_and_verify_user(client, verify=False)

        response = client.get(reverse("secret:list"))

        assert response.status_code == 200


class TestUpdateView:
    def test_auth_required(self, client):
        secret = SecretFactory()
        url = reverse("secret:detail", kwargs={"pk": secret.pk})
        response = client.get(url)

        assert response.status_code == 302
        qs = "?next=" + quote_plus(url)
        assert response.url == reverse("authbroker_client:login") + qs

    def test_superuser_can_view_and_edit_secrets(self, client):
        login_and_verify_user(client, is_superuser=True)
        secret = SecretFactory()

        response = client.get(reverse("secret:detail", kwargs={"pk": secret.pk}))

        assert response.status_code == 200

        response = client.post(
            reverse("secret:detail", kwargs={"pk": secret.pk}), {"name": "hello world"}
        )

        assert response.status_code == 302
        assert response.url == reverse("secret:detail", kwargs={"pk": secret.pk})

        assert Secret.objects.first().name == "hello world"

    def test_user_cannot_view_secret_without_permissions(self, client):
        login_and_verify_user(client)

        secret = SecretFactory()

        response = client.get(reverse("secret:detail", kwargs={"pk": secret.pk}))

        assert response.status_code == 403

    def test_user_cannot_change_view_without_permissions(self, client):
        user = login_and_verify_user(client)

        secret = SecretFactory()

        response = client.post(
            reverse("secret:detail", kwargs={"pk": secret.pk}), {"name": "testing 123"}
        )

        assert response.status_code == 403

        # 'change_secret' permissions are needed
        assign_perm("view_secret", user, secret)

        response = client.post(
            reverse("secret:detail", kwargs={"pk": secret.pk}), {"name": "testing 123"}
        )

        assert response.status_code == 403

    def test_update_success(self, client):
        user = login_and_verify_user(client)

        secret = SecretFactory()

        assign_perm("change_secret", user, secret)

        response = client.post(
            reverse("secret:detail", kwargs={"pk": secret.pk}), {"name": "hello world"}
        )

        assert response.status_code == 302
        assert response.url == reverse("secret:detail", kwargs={"pk": secret.pk})
        secret.refresh_from_db()
        assert secret.name == "hello world"

    @pytest.mark.freeze_time("2020-08-07 00:01:01")
    def test_view_audit_entry(self, client):
        user = login_and_verify_user(client)

        secret = SecretFactory()

        assign_perm("view_secret", user, secret)

        client.get(reverse("secret:detail", kwargs={"pk": secret.pk}))

        assert Audit.objects.count() == 1
        audit = Audit.objects.first()

        assert audit.action == Actions.view_secret.name
        assert audit.timestamp == timezone.now()
        assert audit.user == user
        assert audit.secret == secret

    @pytest.mark.freeze_time("2020-08-07 00:01:01")
    def test_update_audit_entry(self, client):
        user = login_and_verify_user(client)

        secret = SecretFactory()

        assign_perm("change_secret", user, secret)

        client.post(reverse("secret:detail", kwargs={"pk": secret.pk}), {"name": "hello world"})

        assert Audit.objects.count() == 1
        audit = Audit.objects.first()

        assert audit.action == Actions.update_secret.name
        assert audit.timestamp == timezone.now()
        assert audit.user == user
        assert audit.secret == secret


class TestCreateVew:
    def test_auth_required(self, client):
        url = reverse("secret:create")

        response = client.get(url)

        assert response.status_code == 302
        qs = "?next=" + quote_plus(url)
        assert response.url == reverse("authbroker_client:login") + qs

    def test_page_load_unverfied(self, client):
        login_and_verify_user(client, verify=False)

        response = client.get(reverse("secret:create"))

        assert response.status_code == 302
        assert response.url.startswith(reverse("twofactor:verify"))

    def test_redirects_to_update_view_on_success(self, client):
        login_and_verify_user(client)

        response = client.post(reverse("secret:create"), {"name": "test secret"})

        assert Secret.objects.count() == 1
        secret = Secret.objects.first()
        assert secret.name == "test secret"

        assert response.status_code == 302
        assert response.url == reverse("secret:detail", kwargs={"pk": secret.id})

    def test_user_owns_secret(self, client):
        user = login_and_verify_user(client)

        client.post(reverse("secret:create"), {"name": "test secret"})

        assert Secret.objects.count() == 1
        secret = Secret.objects.first()

        assert user.has_perm("view_secret", secret)
        assert user.has_perm("change_secret", secret)

    @pytest.mark.freeze_time("2020-08-07 00:01:01")
    def test_create_audit_entry(self, client):
        user = login_and_verify_user(client)

        client.post(reverse("secret:create"), {"name": "test secret"})

        assert Audit.objects.count() == 1
        audit = Audit.objects.first()
        assert Secret.objects.count() == 1
        secret = Secret.objects.first()

        assert audit.timestamp == timezone.now()
        assert audit.user == user
        assert audit.secret == secret
        assert audit.action == Actions.create_secret.name


class TestSecretPermissionsView:
    def test_page_requires_auth(self, client):
        secret = SecretFactory()
        url = reverse("secret:permissions", kwargs={"pk": secret.pk})
        response = client.get(url)

        qs = "?next=" + quote_plus(url)

        assert response.status_code == 302
        assert response.url == reverse("authbroker_client:login") + qs

    def test_page_requires_2fa_verification(self, client):
        secret = SecretFactory()
        login_and_verify_user(client, verify=False)

        response = client.get(reverse("secret:permissions", kwargs={"pk": secret.pk}))

        assert response.status_code == 302
        assert response.url.startswith(reverse("twofactor:verify"))

    def test_viewing_page_requires_view_permission(self, client):
        login_and_verify_user(client)
        secret = SecretFactory()

        response = client.get(reverse("secret:permissions", kwargs={"pk": secret.pk}))

        assert response.status_code == 403

    def test_successful_page_load(self, client):
        user = login_and_verify_user(client)
        secret = SecretFactory()

        assign_perm("view_secret", user, secret)

        response = client.get(reverse("secret:permissions", kwargs={"pk": secret.pk}))

        assert response.status_code == 200
        assert response.template_name == ["secret/permissions.html"]

    def test_requires_change_permission_to_add_permission(self, client):
        user = login_and_verify_user(client)
        secret = SecretFactory()

        assign_perm("view_secret", user, secret)

        response = client.post(reverse("secret:permissions", kwargs={"pk": secret.pk}), {})

        assert response.status_code == 403

    @pytest.mark.parametrize(
        "permission, expected",
        [
            ("change_secret", {"view_secret", "change_secret"}),
            ("view_secret", {"view_secret"}),
        ],
    )
    def test_add_user_permissions(self, permission, expected, client):

        user = login_and_verify_user(client)

        secret = SecretFactory()

        assign_perm("change_secret", user, secret)

        target_user = UserFactory()

        response = client.post(
            reverse("secret:permissions", kwargs={"pk": secret.pk}),
            {"user": target_user.id, "permission": permission},
        )

        assert response.status_code == 302
        assert set(get_perms(target_user, secret)) == expected

    @pytest.mark.parametrize(
        "permission, expected",
        [
            ("change_secret", {"view_secret", "change_secret"}),
            ("view_secret", {"view_secret"}),
        ],
    )
    def test_add_group_permissions(self, permission, expected, client):
        secret = SecretFactory()

        permission_url = reverse("secret:permissions", kwargs={"pk": secret.pk})

        target_group = GroupFactory()
        user = login_and_verify_user(client)

        assign_perm("change_secret", user, secret)

        response = client.post(
            permission_url,
            {"group": target_group.id, "permission": permission},
        )

        assert response.status_code == 302
        assert response.url == permission_url
        assert set(get_perms(target_group, secret)) == expected

    @pytest.mark.freeze_time("2020-08-07 00:01:01")
    def test_verify_audit_events_are_created(self, client):
        secret = SecretFactory()

        permission_url = reverse("secret:permissions", kwargs={"pk": secret.pk})
        user = login_and_verify_user(client)

        assign_perm("change_secret", user, secret)

        target_user = UserFactory()

        assert Audit.objects.count() == 0
        response = client.post(
            permission_url,
            {"user": target_user.id, "permission": "change_secret"},
        )

        assert response.status_code == 302
        assert response.url == permission_url

        assert Audit.objects.count() == 1
        audit = Audit.objects.first()

        assert audit.user == user
        assert audit.timestamp == timezone.now()
        assert audit.secret == secret
        assert audit.action == Actions.add_permission.name
        assert audit.description == f"Permission level to set change_secret for {target_user}"


class TestSecretPermissionsDeleteView:
    def test_page_requires_auth(self, client):
        secret = SecretFactory()
        url = reverse("secret:delete-permission", kwargs={"pk": secret.pk})
        response = client.get(url)

        qs = "?next=" + quote_plus(url)

        assert response.status_code == 302
        assert response.url == reverse("authbroker_client:login") + qs

    def test_page_requires_2fa_verification(self, client):
        secret = SecretFactory()
        login_and_verify_user(client, verify=False)

        response = client.get(reverse("secret:delete-permission", kwargs={"pk": secret.pk}))

        assert response.status_code == 302
        assert response.url.startswith(reverse("twofactor:verify"))

    def test_viewing_page_requires_change_permission(self, client):
        user = login_and_verify_user(client)
        secret = SecretFactory()

        url = reverse("secret:delete-permission", kwargs={"pk": secret.pk})
        response = client.get(url)

        assert response.status_code == 403

        assign_perm("view_secret", user, secret)

        response = client.get(reverse("secret:delete-permission", kwargs={"pk": secret.pk}))

        assert response.status_code == 403

    def test_load_page(self, client):
        user = login_and_verify_user(client)
        secret = SecretFactory()

        assign_perm("change_secret", user, secret)

        response = client.get(
            reverse("secret:delete-permission", kwargs={"pk": secret.pk})
            + f"?user={user.id}&permission=change_secret"
        )

        assert response.status_code == 200

    def test_delete_user_permission(self, client):
        user = login_and_verify_user(client)
        secret = SecretFactory()

        assign_perm("change_secret", user, secret)

        target_user = UserFactory()
        assign_perm("change_secret", target_user, secret)
        assign_perm("view_secret", target_user, secret)

        response = client.post(
            reverse("secret:delete-permission", kwargs={"pk": secret.pk}),
            {"user": target_user.id},
        )

        assert response.status_code == 302
        assert response.url == reverse("secret:permissions", kwargs={"pk": secret.id})
        assert get_perms(target_user, secret) == []

    def test_delete_group_permissions(self, client):
        user = login_and_verify_user(client)
        secret = SecretFactory()

        assign_perm("change_secret", user, secret)

        target_group = GroupFactory()
        assign_perm("change_secret", target_group, secret)
        assign_perm("view_secret", target_group, secret)

        response = client.post(
            reverse("secret:delete-permission", kwargs={"pk": secret.pk}),
            {"group": target_group.id},
        )

        assert response.status_code == 302
        assert response.url == reverse("secret:permissions", kwargs={"pk": secret.id})
        assert get_perms(target_group, secret) == []

    @pytest.mark.freeze_time("2020-08-07 00:01:01")
    def test_audit_event_is_created(self, client):
        user = login_and_verify_user(client)
        secret = SecretFactory()

        assign_perm("change_secret", user, secret)

        target_group = GroupFactory()
        assign_perm("change_secret", target_group, secret)
        assign_perm("view_secret", target_group, secret)

        response = client.post(
            reverse("secret:delete-permission", kwargs={"pk": secret.pk}),
            {"group": target_group.id, "permission": "view_secret"},
        )

        assert response.status_code == 302

        assert Audit.objects.count() == 1
        audit = Audit.objects.first()

        assert audit.user == user
        assert audit.timestamp == timezone.now()
        assert audit.secret == secret
        assert audit.description == f"Access removed for {target_group}"


class TestSecretAuditView:
    def test_page_requires_auth(self, client):
        secret = SecretFactory()

        url = reverse("secret:audit", kwargs={"pk": secret.pk})
        response = client.get(url)

        qs = "?next=" + quote_plus(url)

        assert response.status_code == 302
        assert response.url == reverse("authbroker_client:login") + qs

    def test_page_requires_2fa_verification(self, client):
        secret = SecretFactory()
        login_and_verify_user(client, verify=False)

        response = client.get(reverse("secret:audit", kwargs={"pk": secret.pk}))

        assert response.status_code == 302
        assert response.url.startswith(reverse("twofactor:verify"))

    def test_viewing_page_requires_view_permission(self, client):
        login_and_verify_user(client)
        secret = SecretFactory()

        response = client.get(reverse("secret:audit", kwargs={"pk": secret.pk}))

        assert response.status_code == 403

    def test_page_load(self, client):
        user = login_and_verify_user(client)
        secret = SecretFactory()

        assign_perm("view_secret", user, secret)

        response = client.get(reverse("secret:audit", kwargs={"pk": secret.pk}))

        assert response.status_code == 200
        assert response.template_name == ["secret/secret_audit.html"]


class TestMFAClientSetup:
    def test_page_requires_auth(self, client):
        secret = SecretFactory()

        url = reverse("secret:mfa_setup", kwargs={"pk": secret.pk})
        response = client.get(url)

        qs = "?next=" + quote_plus(url)

        assert response.status_code == 302
        assert response.url == reverse("authbroker_client:login") + qs

    def test_page_requires_2fa_verification(self, client):
        secret = SecretFactory()
        login_and_verify_user(client, verify=False)

        response = client.get(reverse("secret:mfa_setup", kwargs={"pk": secret.pk}))

        assert response.status_code == 302
        assert response.url.startswith(reverse("twofactor:verify"))

    def test_viewing_page_requires_change_permission(self, client):
        user = login_and_verify_user(client)
        secret = SecretFactory()

        response = client.get(reverse("secret:mfa_setup", kwargs={"pk": secret.pk}))

        assert response.status_code == 403

        assign_perm("view_secret", user, secret)

        response = client.get(reverse("secret:mfa_setup", kwargs={"pk": secret.pk}))

        assert response.status_code == 403

    def test_invalid_code(self, client):
        user = login_and_verify_user(client)
        secret = SecretFactory()

        assign_perm("change_secret", user, secret)

        response = client.post(
            reverse("secret:mfa_setup", kwargs={"pk": secret.pk}),
            {"mfa_string": "invalid-otp-code"},
        )

        secret.refresh_from_db()
        assert response.status_code == 200
        assert not secret.mfa_string

    def test_setup_success(self, client):
        mfa_string = "otpauth://totp/Someapp%3Asome@user.com?secret=SNVQHZZUNABGV7DP3M4UI57OH7YZWNFI&algorithm=SHA1&digits=6&period=30&issuer=Someapp"  # noqa
        user = login_and_verify_user(client)
        secret = SecretFactory()

        assign_perm("change_secret", user, secret)

        response = client.post(
            reverse("secret:mfa_setup", kwargs={"pk": secret.pk}), {"mfa_string": mfa_string}
        )

        secret.refresh_from_db()
        assert response.status_code == 302
        assert response.url == reverse("secret:mfa", kwargs={"pk": secret.pk})
        assert secret.mfa_string == mfa_string


class TestMFAClient:
    def test_page_requires_auth(self, client):
        secret = SecretFactory()

        url = reverse("secret:mfa_setup", kwargs={"pk": secret.pk})
        response = client.get(url)

        qs = "?next=" + quote_plus(url)

        assert response.status_code == 302
        assert response.url == reverse("authbroker_client:login") + qs

    def test_page_requires_2fa_verification(self, client):
        secret = SecretFactory()
        login_and_verify_user(client, verify=False)

        response = client.get(reverse("secret:mfa_setup", kwargs={"pk": secret.pk}))

        assert response.status_code == 302
        assert response.url.startswith(reverse("twofactor:verify"))

    def test_page_requires_view_permission(self, client):
        login_and_verify_user(client)
        secret = SecretFactory()

        response = client.get(reverse("secret:mfa_setup", kwargs={"pk": secret.pk}))

        assert response.status_code == 403

    def test_shows_setup_link_if_no_mfa_configured(self, client):
        user = login_and_verify_user(client)

        secret = SecretFactory()

        assign_perm("view_secret", user, secret)
        assign_perm("change_secret", user, secret)

        response = client.get(reverse("secret:mfa", kwargs={"pk": secret.pk}))

        assert response.status_code == 200

        link_html = '<a class="btn btn-danger" href="{}" role="button">Setup MFA client</a>'.format(
            reverse("secret:mfa_setup", kwargs={"pk": secret.pk})
        )

        assert link_html in response.content.decode("utf-8")

    def test_generate_token(self, client):

        mfa_string = "otpauth://totp/someapp%3Asome@email.com?secret=SNVQHZZUNABGV7DP3M4UI57OH7YZWNFI&algorithm=SHA1&digits=6&period=30&issuer=someapp"  # noqa

        user = login_and_verify_user(client)
        secret = SecretFactory(mfa_string=mfa_string)

        assign_perm("view_secret", user, secret)

        response = client.get(reverse("secret:mfa", kwargs={"pk": secret.pk}))
        content = response.content.decode("utf-8")

        assert response.status_code == 200
        code = re.search(r"\>(\d{6})\<", content).groups()[0]

        assert secret.verify_otp(code)

    def test_audit(self, client):
        mfa_string = "otpauth://totp/someapp%3Asome@email.com?secret=SNVQHZZUNABGV7DP3M4UI57OH7YZWNFI&algorithm=SHA1&digits=6&period=30&issuer=someapp"  # noqa

        user = login_and_verify_user(client)
        secret = SecretFactory(mfa_string=mfa_string)

        assign_perm("view_secret", user, secret)

        assert Audit.objects.count() == 0


class TestMFAClientDelete:
    def test_page_requires_auth(self, client):
        secret = SecretFactory()

        url = reverse("secret:mfa_setup", kwargs={"pk": secret.pk})
        response = client.get(url)

        qs = "?next=" + quote_plus(url)

        assert response.status_code == 302
        assert response.url == reverse("authbroker_client:login") + qs

    def test_page_requires_2fa_verification(self, client):
        secret = SecretFactory()
        login_and_verify_user(client, verify=False)

        response = client.get(reverse("secret:mfa_setup", kwargs={"pk": secret.pk}))

        assert response.status_code == 302
        assert response.url.startswith(reverse("twofactor:verify"))

    def test_page_requires_change_permission(self, client):
        user = login_and_verify_user(client)
        secret = SecretFactory()

        response = client.get(reverse("secret:mfa_delete", kwargs={"pk": secret.pk}))

        assert response.status_code == 403

        assign_perm("view_secret", user, secret)

        response = client.get(reverse("secret:mfa_delete", kwargs={"pk": secret.pk}))

        assert response.status_code == 403

    def test_success(self, client):
        user = login_and_verify_user(client)
        secret = SecretFactory()

        secret.mfa_string = "test-string"
        secret.save()

        assign_perm("change_secret", user, secret)

        response = client.post(reverse("secret:mfa_delete", kwargs={"pk": secret.pk}))

        secret.refresh_from_db()
        assert response.status_code == 302
        assert response.url == reverse("secret:mfa", kwargs={"pk": secret.pk})
        assert not secret.mfa_string
