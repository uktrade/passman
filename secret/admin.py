from django.contrib import admin

from guardian.admin import GuardedModelAdmin

from .models import Secret


class SecretAdmin(GuardedModelAdmin):

    list_display = ('created', 'last_updated', 'created_by', 'name',)
    readonly_fields = ('created', 'last_updated',)

    ordering = ('created',)


admin.site.register(Secret, SecretAdmin)
