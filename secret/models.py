import uuid

from django.db import models
from django.urls import reverse

from django_cryptography.fields import encrypt
from guardian.models import UserObjectPermissionBase
from guardian.models import GroupObjectPermissionBase
from guardian.shortcuts import (
    assign_perm,
    get_user_perms,
    get_group_perms,
    remove_perm,
)

import pyotp

from user.models import User


class Secret(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey("user.User", on_delete=models.SET_NULL, null=True)

    deleted = models.BooleanField(default=False)

    name = models.CharField(max_length=255)

    url = models.URLField(blank=True)
    username = models.CharField(max_length=255, blank=True)
    password = encrypt(models.CharField(max_length=255, blank=True))
    details = encrypt(models.TextField(blank=True))

    mfa_string = encrypt(models.CharField(max_length=255, blank=True))

    @property
    def mfa_code(self):
        if hasattr(self, "mfaclient"):
            return self.mfaclient.generate_code() if self.mfaclient else None

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("secret:detail", args=[self.id])

    def _get_perms(self, target):
        if isinstance(target, User):
            return get_user_perms(target, self)
        else:
            return get_group_perms(target, self)

    def set_permission(self, target, permission):
        current_perms = set(self._get_perms(target))

        required_perms = (
            {"view_secret", "change_secret"} if permission == "change_secret" else {"view_secret"}
        )

        for permission in list(required_perms.difference(current_perms)):
            assign_perm(permission, target, self)

        for permission in list(current_perms.difference(required_perms)):
            remove_perm(permission, target, self)

    def remove_permissions(self, target):
        permissions = self._get_perms(target)

        for perm in permissions:
            remove_perm(perm, target, self)

    def get_otp(self):
        if not self.mfa_string:
            return None

        otp = pyotp.parse_uri(self.mfa_string)

        # the library fails to cast the interval field to a number,
        # despite requiring that the field be a number
        otp.interval = int(otp.interval)

        return otp

    def verify_otp(self, code):
        return self.get_otp().verify(code)

    def generate_otp_code(self):
        otp = self.get_otp()

        return None if not otp else otp.now()


class SecretUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(Secret, on_delete=models.CASCADE)


class SecretGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(Secret, on_delete=models.CASCADE)
