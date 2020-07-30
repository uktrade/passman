from guardian.admin import GuardedModelAdmin

from core.admin import admin_site
from .models import Secret


class SecretAdmin(GuardedModelAdmin):

    list_display = (
        "created",
        "last_updated",
        "created_by",
        "name",
    )
    readonly_fields = (
        "created",
        "last_updated",
    )

    ordering = ("created",)


admin_site.register(Secret, SecretAdmin)
