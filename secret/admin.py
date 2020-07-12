from django.contrib import admin

from .models import Secret


class SecretAdmin(admin.ModelAdmin):

    list_display = ('created', 'last_updated', 'created_by', 'name',)
    readonly_fields = ('created', 'last_updated',)

    ordering = ('created',)


admin.site.register(Secret, SecretAdmin)
