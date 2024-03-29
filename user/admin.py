from django import forms
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from user.models import User

from core.admin import admin_site


class UserCreationForm(forms.ModelForm):
    """A form for creating new users."""

    class Meta:
        model = User
        fields = ("email",)


class UserChangeForm(forms.ModelForm):
    """A form for updating users. """

    class Meta:
        model = User
        fields = ("email", "is_active", "is_superuser")


class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ("email", "is_superuser", "is_active")
    list_filter = ("is_superuser", "is_active", "groups")

    autocomplete_fields = ("groups",)

    fieldsets = (
        (None, {"fields": ("email",)}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        ("Permissions", {"fields": ("is_staff", "is_superuser", "is_active")}),
        ("Groups", {"fields": ("groups",)}),
    )

    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("email",),}),)
    search_fields = ("email",)
    ordering = ("email",)
    filter_horizontal = ()


admin_site.register(User, UserAdmin)
