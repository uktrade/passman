import uuid

from django.db import models
from django.db.models import Q
from django.urls import reverse


class SecretManager(models.Manager):
    def filter_by_group(self, group):
        return self.filter(Q(owner_group=group) | Q(viewer_groups=group))


class Secret(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey('user.User', on_delete=models.PROTECT, null=True)

    owner_group = models.ForeignKey('auth.Group', related_name='owner_group', on_delete=models.PROTECT, null=True)
    viewer_groups = models.ManyToManyField('auth.Group', related_name='viewer_groups')

    name = models.CharField(max_length=255)

    url = models.URLField(blank=True)
    username = models.CharField(max_length=255, blank=True)
    password = models.CharField(max_length=255, blank=True)
    details = models.TextField(blank=True)

    objects = SecretManager()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('secret:detail', args=[self.id])
