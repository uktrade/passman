from functools import partial
import io

from django.contrib import messages
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
            context['qrcode'] = self.make_qrcode()

        return context

    def form_valid(self, form):

        messages.info(self.request, 'You have enabled 2-factor authentication')

        device = self.get_device()
        device.confirmed = True
        device.save()

        return super().form_valid(form)


class TwoFactorVerifyView(FormView):
    form_class = OTPTokenForm
    template_name = 'twofactor/verify.html'
    success_url = reverse_lazy('secret:list')

    def get_form_class(self):
        return partial(self.form_class, self.request.user)

    def form_valid(self, form):
        login(self.request, self.request.user.otp_device)

        return super().form_valid(form)

    def get_success_url(self):
        if 'next' in self.request.GET:
            # TODO: make sure this is validated safe
            return self.request.GET['next']

        return super().get_success_urL()
