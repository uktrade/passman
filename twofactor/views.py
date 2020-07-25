from functools import partial
import io

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.views import SuccessURLAllowedHostsMixin
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from django.urls import reverse_lazy
from django.views.generic import FormView

from django_otp import login
from django_otp.plugins.otp_totp.models import TOTPDevice
import qrcode
import qrcode.image.svg

from .forms import OTPTokenForm, OTPVerifyForm


class TwoFactorEnrollView(FormView):
    form_class = OTPVerifyForm
    template_name = 'twofactor/enroll.html'
    success_url = reverse_lazy('secret:list')
    device = None

    def get_device(self):
        if not self.device:
            self.device, _ = TOTPDevice.objects.get_or_create(
                user=self.request.user,
                defaults={
                    'confirmed': False,
                    'name': 'TOTP device',
                }
            )

        return self.device

    def get_form_class(self):
        return partial(self.form_class, self.get_device())

    def make_qrcode(self, device):
        img = io.BytesIO()
        qrcode.make(device.config_url, image_factory=qrcode.image.svg.SvgImage).save(img)
        img.seek(0)

        return img

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        device = self.get_device()

        context['device_confirmed'] = device.confirmed

        if not device.confirmed:
            context['qrcode'] = self.make_qrcode(device)

        return context

    def form_valid(self, form):

        messages.info(self.request, 'You have enabled 2-factor authentication')

        device = self.get_device()
        device.confirmed = True
        device.save()

        return super().form_valid(form)


class TwoFactorVerifyView(SuccessURLAllowedHostsMixin, FormView):
    form_class = OTPTokenForm
    template_name = 'twofactor/verify.html'
    success_url = reverse_lazy('secret:list')
    redirect_field_name = REDIRECT_FIELD_NAME

    def get_form_class(self):
        return partial(self.form_class, self.request.user)

    def form_valid(self, form):
        login(self.request, self.request.user.otp_device)

        return super().form_valid(form)

    def get_redirect_url(self):
        """Return the user-originating redirect URL if it's safe."""
        redirect_to = self.request.POST.get(
            self.redirect_field_name,
            self.request.GET.get(self.redirect_field_name, '')
        )
        url_is_safe = url_has_allowed_host_and_scheme(
            url=redirect_to,
            allowed_hosts=self.get_success_url_allowed_hosts(),
            require_https=self.request.is_secure(),
        )
        return redirect_to if url_is_safe else ''

    def get_success_url(self):

        url = self.get_redirect_url()

        return url or self.success_url
