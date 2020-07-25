from django.db import models

from .types import StrEnum


class Actions(StrEnum):
    created_secret = 'Created'
    updated_secret = 'Updated'
    viewed_secret = 'Viewed'
    add_permission = 'Add permission'
    remove_permission = 'Remove permission'


class Audit(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey('user.User', on_delete=models.PROTECT)
    secret = models.ForeignKey('secret.Secret', on_delete=models.PROTECT)
    action = models.CharField(choices=Actions.list(), max_length=255)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name_plural = 'audit'


def create_audit_event(user, action, description=None, secret=None, repeat_once=False):
    """
    Create an audit event
    """

    Audit.objects.create(
        user=user,
        action=action,
        description=description or '',
        secret=secret,
    )
