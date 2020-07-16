from django import forms
from django.utils.safestring import mark_safe

from crispy_forms.bootstrap import PrependedAppendedText, AppendedText, FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Field, Layout, Submit, Row, Submit

from .models import Secret


def clipboard_html(input_id):
    return mark_safe(f'<span copy="{input_id}" class="fa fa-clipboard copy-to-clipboard"></span>')

def showpassword_html(input_id):
    return mark_safe(
        f'<span toggle="{input_id}" class="fa fa-fw fa-eye-slash field-icon toggle-password"></span>')


class SecretForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(render_value=True), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('name'),
                Column(AppendedText('url', clipboard_html('#id_url'))),
                css_class='form-row'
            ),
            Row(
                Column(AppendedText('username', clipboard_html('#id_username'))),
                Column(PrependedAppendedText(
                    'password', showpassword_html('#id_password'), clipboard_html('#id_password'))),
                css_class='form-row',
            ),
            'details',
            'owner_group',
            'viewer_groups',
            FormActions(
                Submit('save', 'Save changes'),
            ),
        )

    class Meta:
        model = Secret
        fields = [
            'name',
            'url',
            'username',
            'password',
            'details',
            'owner_group',
            'viewer_groups',
        ]
