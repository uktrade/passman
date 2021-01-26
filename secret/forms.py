from django import forms
from django.utils.safestring import mark_safe
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model

from PIL import Image
import pyotp
from pyzbar import pyzbar

from crispy_forms.bootstrap import PrependedAppendedText, AppendedText, FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Field, Layout, Row, Submit

from .models import Secret


EDIT_SECRET_PERMISSION = "change_secret"
VIEW_SECRET_PERMISSION = "view_secret"

PERMISSION_CHOICES = (
    (VIEW_SECRET_PERMISSION, "View"),
    (EDIT_SECRET_PERMISSION, "Change"),
)


def clipboard_html(input_id):
    return mark_safe(f'<span copy="{input_id}" class="fa fa-clipboard copy-to-clipboard"></span>')


def showpassword_html(input_id):
    return mark_safe(
        f'<span toggle="{input_id}" class="fa fa-fw fa-eye-slash field-icon toggle-password"></span>'
    )


class SecretUpdateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(render_value=True), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column("name"),
                Column(AppendedText("url", clipboard_html("#id_url"))),
                css_class="form-row",
            ),
            Row(
                Column(AppendedText("username", clipboard_html("#id_username"))),
                Column(
                    PrependedAppendedText(
                        "password",
                        showpassword_html("#id_password"),
                        clipboard_html("#id_password"),
                    )
                ),
                css_class="form-row",
            ),
            "details",
            FormActions(Submit("save", "Update secret"),),
        )

    class Meta:
        model = Secret
        fields = [
            "name",
            "url",
            "username",
            "password",
            "details",
        ]


class SecretCreateForm(SecretUpdateForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper.layout[-1] = FormActions(Submit("save", "Create secret"),)


class SecretPermissionsForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=get_user_model().objects.all().exclude(email="AnonymousUser"),
        required=False,
        widget=forms.HiddenInput(),
    )
    group = forms.ModelChoiceField(
        queryset=Group.objects.all().order_by("name"), required=False, widget=forms.HiddenInput(),
    )
    permission = forms.ChoiceField(choices=PERMISSION_CHOICES, widget=forms.HiddenInput(),)

    def __init__(self, *args, update_permission=False, **kwargs):
        super().__init__(*args, **kwargs)

        if update_permission:
            self.fields["permission"].widget = forms.Select()
            self.fields["permission"].choices = PERMISSION_CHOICES

            self.helper = FormHelper()
            self.helper.form_class = "update_perms"
            self.helper.form_show_labels = False
            self.helper.layout = Layout(
                "user", "group", Field("permission", css_class="form-control-sm"),
            )

    def clean(self):
        cleaned_data = super().clean()

        if not cleaned_data["user"] and not cleaned_data["group"]:
            raise forms.ValidationError("Select either a user or a group")

        return cleaned_data


class SecretGroupPermissionsForm(forms.Form):
    group = forms.ModelChoiceField(queryset=Group.objects.all().order_by("name"))
    permission = forms.ChoiceField(choices=PERMISSION_CHOICES)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column("group"), Column("permission"), css_class="form-row"),
            FormActions(Submit("add", "Add"),),
        )


class SecretUserPermissionsForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=get_user_model().objects.all().exclude(email="AnonymousUser")
    )
    permission = forms.ChoiceField(choices=PERMISSION_CHOICES)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column("user"), Column("permission"), css_class="form-row"),
            FormActions(Submit("add", "Add"),),
        )


class MFAClientSetupForm(forms.Form):
    qr_code = forms.ImageField(
        label="QR Code",
        required=False,
        help_text="Screen shot and upload an image of the MFA QR code",
    )
    mfa_string = forms.CharField(
        label="MFA String",
        max_length=255,
        required=False,
        help_text="Or, manually enter the MFA string",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("qr_code"), Field("mfa_string"), FormActions(Submit("Enable", "Enable"),),
        )

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data["qr_code"] and not cleaned_data["mfa_string"]:
            raise forms.ValidationError(
                "Either upload an screenshot of an QR code OR enter "
                "the MFA code string manually; only one field is required."
            )

        if cleaned_data["qr_code"]:
            decoded = self.extract_code_from_qr_image(cleaned_data["qr_code"])

            if not decoded:
                raise form.ValidationError("Invalid QR code")

            if self.is_valid_otp_string(decoded):
                cleaned_data["mfa_string"] = decoded
                return cleaned_data

        if cleaned_data["mfa_string"]:
            if self.is_valid_otp_string(cleaned_data["mfa_string"]):
                return cleaned_data

        raise forms.ValidationError("Unable to validate QR code")

    def is_valid_otp_string(self, mfa_string):
        try:
            pyotp.parse_uri(mfa_string)
            return True
        except ValueError:
            return False

    def extract_code_from_qr_image(self, image_field):
        image = Image.open(image_field)
        decoded = pyzbar.decode(image)

        if len(decoded):
            if decoded[0].type == "QRCODE":
                return decoded[0].data.decode("utf-8")

        return None
