import uuid

from django.db import models
from django.urls import reverse

from django_cryptography.fields import encrypt


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
    password = encrypt(models.CharField(max_length=255, blank=True))
    details = encrypt(models.TextField(blank=True))

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('secret:detail', args=[self.id])

    class Meta:
        ordering = ('name',)
