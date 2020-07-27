from django import forms

from crispy_forms.bootstrap import PrependedAppendedText, AppendedText, FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Field, Layout, Submit, Row, Submit

from django_otp.forms import OTPAuthenticationFormMixin


class OTPVerifyForm(forms.Form):
    otp_token = forms.CharField(label='Enter token', required=False)

    _device = None

    def __init__(self, device, *args, **kwargs):
        self._device = device

        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('otp_token', css_class='w-25'),
            FormActions(
                Submit('save', 'Verify'),
            ),
        )

    def clean_otp_token(self):
        token = self.cleaned_data['otp_token']
        if not self._device.verify_token(token):
            raise forms.ValidationError('Invalid token')

        return token


class OTPTokenForm(OTPAuthenticationFormMixin, forms.Form):
    otp_device = forms.CharField(required=False, widget=forms.HiddenInput())
    otp_token = forms.CharField(required=False, widget=forms.TextInput(attrs={'autocomplete': 'off'}))
    otp_challenge = forms.CharField(required=False, widget=forms.HiddenInput())

    def __init__(self, user, request=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.user = user
        self.fields['otp_device'].initial = self.device_choices(user)[0]

        self.fields['otp_token'].label = 'Enter your token'

        self.helper = FormHelper()
        self.helper.layout = Layout(
            'otp_device',
            Field('otp_token', css_class='w-25'),
            'otp_challenge',
            FormActions(
                Submit('save', 'Verify'),
            ),
        )

    def clean(self):
        super().clean()

        self.clean_otp(self.user)

        return self.cleaned_data

    def get_user(self):
        return self.user
