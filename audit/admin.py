from django.contrib import admin

from core.admin import admin_site
from .models import Audit


class AuditAdmin(admin.ModelAdmin):

    list_display = ("timestamp", "user", "secret", "action")
    list_filter = ("user", "secret", "action")

    ordering = ("timestamp",)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin_site.register(Audit, AuditAdmin)
