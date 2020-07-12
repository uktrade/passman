from django.forms import ModelForm

from .models import Secret


class SecretForm(ModelForm):
    class Meta:
        model = Secret
        fields = [
            'name',
            'url',
            'username',
            'password',
            'details',
            'owner_group',
            'viewer_groups',
        ]
