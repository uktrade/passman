from django import forms

from .models import Secret


class SecretForm(forms.ModelForm):
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
