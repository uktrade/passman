from guardian.admin import GuardedModelAdmin

from core.admin import admin_site  # noqa: F401
from .models import Secret  # noqa: F401


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

    exclude = ("password",)

    ordering = ("created",)


# All password editing should be done through the interface
# admin_site.register(Secret, SecretAdmin)
