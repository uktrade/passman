import pytest

from django.urls import reverse

from user.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestTwoFactorEnrollView:
    def test_auth_required(self, client):
        response = client.get(reverse("twofactor:enroll"))

        assert response.status_code == 302
        assert response.url == reverse("authbroker_client:login")

    def test_load_page_creates_unconfirmed_totp_device(self, client):
        user = UserFactory(is_active=True)

        assert user.totpdevice_set.count() == 0

        client.force_login(user)
        response = client.get(reverse("twofactor:enroll"))

        assert user.totpdevice_set.count() == 1
        assert not user.totpdevice_set.first().confirmed

        assert response.status_code == 200
        assert response.template_name == ["twofactor/enroll.html"]

    def test_submit_wrong_code_results_in_error(self, client):
        user = UserFactory(is_active=True)
        client.force_login(user)

        # create the device
        client.get(reverse("twofactor:enroll"))

        response = client.post(reverse("twofactor:enroll"), {"code": "123456"})
        html_content = response.content.decode("utf-8")

        assert "Invalid token" in html_content

    def test_submit_correct_code_comfirms_device(self, client, mocker):
        user = UserFactory(is_active=True)
        client.force_login(user)

        # create the device
        client.get(reverse("twofactor:enroll"))

        verify_token = mocker.patch("django_otp.plugins.otp_totp.models.TOTPDevice.verify_token")
        verify_token.return_value = True

        response = client.post(reverse("twofactor:enroll"), {"code": "fake-code"})

        assert response.status_code == 302
        assert response.url == reverse("secret:list")

        assert user.totpdevice_set.count() == 1
        assert user.totpdevice_set.first().confirmed

    def test_device_already_confirmed(self, client):
        """Check that the verification form has been removed"""

        user = UserFactory(is_active=True, two_factor_enabled=True)

        user.totpdevice_set.all().update(confirmed=True)

        client.force_login(user)
        response = client.get(reverse("twofactor:enroll"))
        html_content = response.content.decode("utf-8")
        assert "You have already enabled 2-factor authentication." in html_content


class TestTwoFactorVerifyView:
    def test_auth_required(self, client):
        response = client.get(reverse("twofactor:enroll"))

        assert response.status_code == 302
        assert response.url == reverse("authbroker_client:login")

    def test_requires_confirmed_device(self, client):
        user = UserFactory(is_active=True)

        client.force_login(user)

        response = client.get(reverse("twofactor:verify"))

        assert response.status_code == 302
        assert response.url == reverse("twofactor:enroll")

    def test_invalid_code(self, client):
        user = UserFactory(is_active=True, two_factor_enabled=True)

        client.force_login(user)

        response = client.post(reverse("twofactor:verify"), {"otp_token": "wrong-token"})

        assert response.status_code == 200
        html_content = response.content.decode("utf-8")

        assert "Invalid token. Please make sure you have entered it correctly." in html_content

    def test_valid_code(self, client, mocker):
        user = UserFactory(is_active=True, two_factor_enabled=True)

        verify_token = mocker.patch("django_otp.forms.OTPAuthenticationFormMixin._verify_token")
        verify_token.return_value = user.totpdevice_set.first()

        client.force_login(user)

        response = client.post(reverse("twofactor:verify"), {"otp_token": "fake-token"})

        assert response.status_code == 302
        assert response.url == reverse("secret:list")
        assert client.session["otp_device_id"] == user.totpdevice_set.first().persistent_id
