import datetime as dt
import pytest

from django.utils import timezone

from user.tests.factories.user import UserFactory

from audit.models import Actions, Audit, create_audit_event

pytestmark = pytest.mark.django_db


@pytest.mark.freeze_time('2020-07-25 12:00:01')
def test_create_audit_event_report_once(settings, freezer):
    user = UserFactory()
    create_audit_event(user, Actions.viewed_secret, description='I viewed a secret', secret=None, report_once=True)

    assert Audit.objects.count() == 1

    create_audit_event(user, Actions.viewed_secret, description='I viewed another secret', secret=None, report_once=True)

    assert Audit.objects.count() == 1

    # different action - so it should be created
    create_audit_event(user, Actions.created_secret, description='I created a secret', secret=None, report_once=True)

    freezer.move_to(dt.datetime.now() + dt.timedelta(minutes=settings.AUDIT_EVENT_REPEAT_AFTER_MINUTES + 5))

    create_audit_event(user, Actions.viewed_secret, description='I viewed another secret', secret=None, report_once=True)

    assert Audit.objects.count() == 3


@pytest.mark.freeze_time('2020-07-25 12:00:01')
def test_create_audit_event_recurring():

    user = UserFactory()
    create_audit_event(user, Actions.viewed_secret, description='I viewed a secret', secret=None)

    assert Audit.objects.count() == 1

    create_audit_event(user, Actions.viewed_secret, description='I viewed a secret', secret=None)

    assert Audit.objects.count() == 2


@pytest.mark.freeze_time('2020-07-25 12:00:01')
def test_create_audit_event():

    user = UserFactory()
    create_audit_event(user, Actions.viewed_secret, description='I viewed a secret', secret=None)

    audit = Audit.objects.first()

    assert audit.timestamp == timezone.now()
    assert audit.user == user
    assert audit.action == Actions.viewed_secret.name
    assert audit.description == 'I viewed a secret'
    assert not audit.secret
