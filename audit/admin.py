from django.contrib import admin

from .models import Audit


class AuditAdmin(admin.ModelAdmin):

    list_display = ("timestamp", "user", "secret", "action")
    list_filter = ("user", "secret", "action")

    ordering = ("timestamp",)

    def has_add_permission(self, request, obj=None):
        return False


admin.site.register(Audit, AuditAdmin)
