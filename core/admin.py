from django.contrib.admin.sites import AdminSite
from django.contrib.auth.admin import Group, GroupAdmin

from django_otp.plugins.otp_totp.admin import TOTPDeviceAdmin, TOTPDevice


class OTPAdminSite(AdminSite):
    def __init__(self, name="otpadmin"):
        super().__init__(name)

    def has_permission(self, request):
        """
        In addition to the default requirements, this only allows access to
        users who have been verified by a registered OTP device.
        """
        return super().has_permission(request) and request.user.is_verified()


admin_site = OTPAdminSite()
admin_site.register(Group, GroupAdmin)

admin_site.register(TOTPDevice, TOTPDeviceAdmin)
