from django.contrib import admin
from django import forms
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from user.models import User


class UserCreationForm(forms.ModelForm):
    """A form for creating new users."""

    class Meta:
        model = User
        fields = ('email',)


class UserChangeForm(forms.ModelForm):
    """A form for updating users. """

    class Meta:
        model = User
        fields = ('email', 'is_active', 'is_superuser')


class UserAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ('email', 'is_superuser', 'is_active')
    list_filter = ('is_superuser', 'is_active')

    fieldsets = (
        (None, {'fields': ('email',)}),
        ('Personal info', {'fields': ('first_name','last_name')}),
        ('Permissions', {'fields': ('is_staff','is_superuser', 'is_active')}),
        ('Groups', {'fields': ('groups',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email',),
        }),
    )
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()


admin.site.register(User, UserAdmin)
