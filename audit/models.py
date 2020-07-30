import datetime as dt
from django.db import models

from django.utils import timezone
from django.conf import settings

from .types import StrEnum


class Actions(StrEnum):
    created_secret = "Created"
    updated_secret = "Updated"
    viewed_secret = "Viewed"
    add_permission = "Add permission"
    remove_permission = "Remove permission"


class Audit(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey("user.User", on_delete=models.PROTECT)
    secret = models.ForeignKey("secret.Secret", on_delete=models.PROTECT, null=True, blank=True)
    action = models.CharField(choices=Actions.list(), max_length=255)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name_plural = "audit"


def create_audit_event(user, action: Actions, description=None, secret=None, report_once=False):
    """
    Create an audit event

    If `report_once` is True, then the event will not be created if an event with the same user & action exists
    within the `settings.AUDIT_EVENT_REPEAT_AFTER_MINUTES` period.
    """

    if report_once:
        report_window_start = timezone.now() - dt.timedelta(
            minutes=settings.AUDIT_EVENT_REPEAT_AFTER_MINUTES
        )
        if Audit.objects.filter(
            user=user, action=action.name, timestamp__gte=report_window_start
        ).exists():
            return

    Audit.objects.create(
        user=user, action=action.name, description=description or "", secret=secret,
    )
