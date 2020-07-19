from django.db import models
from django.contrib.auth.models import AbstractBaseUser, Group, PermissionsMixin
from django.utils.translation import ugettext_lazy as _

from guardian.mixins import GuardianUserMixin


class User(AbstractBaseUser, PermissionsMixin, GuardianUserMixin):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    created = models.DateTimeField(
        _('created'),
        auto_now_add=True,
    )

    last_accessed = models.DateTimeField(
        _('last accessed'),
        blank=True,
        null=True,
    )

    email = models.EmailField(
        _('email'), unique=True,
    )

    first_name = models.CharField(
        _('first name'), max_length=50, blank=True
    )

    last_name = models.CharField(
        _('last name'), max_length=50, blank=True
    )

    is_active = models.BooleanField(
        _('is active'),
        default=False,
        help_text=_('Designates whether the user can log in.'),
    )

    is_staff = models.BooleanField(
        _('is staff'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )

    def __str__(self):
        return self.email

    def get_permitted_groups(self):
        """Return a list of groups that this user is allowed to access"""

        if self.is_superuser:
            return Group.objects.all().order_by('name')
        else:
            return self.groups.all().order_by('name')

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'
