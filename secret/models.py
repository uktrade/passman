import uuid

from django.db import models
from django.urls import reverse

from django_cryptography.fields import encrypt
from guardian.models import UserObjectPermissionBase
from guardian.models import GroupObjectPermissionBase
from guardian.shortcuts import (
    assign_perm,
    get_perms,
    remove_perm,
)


class Secret(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey("user.User", on_delete=models.SET_NULL, null=True)

    name = models.CharField(max_length=255)

    url = models.URLField(blank=True)
    username = models.CharField(max_length=255, blank=True)
    password = encrypt(models.CharField(max_length=255, blank=True))
    details = encrypt(models.TextField(blank=True))

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("secret:detail", args=[self.id])

    class Meta:
        ordering = ("name",)

    def set_permission(self, target, permission):
        current_perms = set(get_perms(target, self))

        required_perms = (
            {"view_secret", "change_secret"} if permission == "change_secret" else {"view_secret"}
        )

        for permission in list(required_perms.difference(current_perms)):
            assign_perm(permission, target, self)

        for permission in list(current_perms.difference(required_perms)):
            remove_perm(permission, target, self)

    def remove_permissions(self, target):
        permissions = get_perms(target, self)

        for perm in permissions:
            remove_perm(perm, target, self)


class SecretUserObjectPermission(UserObjectPermissionBase):
    content_object = models.ForeignKey(Secret, on_delete=models.CASCADE)


class SecretGroupObjectPermission(GroupObjectPermissionBase):
    content_object = models.ForeignKey(Secret, on_delete=models.CASCADE)
