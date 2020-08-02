from django import forms
from django.utils.safestring import mark_safe
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model

from crispy_forms.bootstrap import PrependedAppendedText, AppendedText, FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Layout, Row, Submit

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
