from django.contrib.auth.models import Group

import django_filters

from guardian.shortcuts import get_objects_for_group, get_objects_for_user

from .models import Secret


class SecretFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains', distinct=True)
    group = django_filters.CharFilter(method='filter_by_group', distinct=True)
    me = django_filters.CharFilter(method='shared_directly', distinct=True)

    o = django_filters.OrderingFilter(
        fields=(
            ('name', 'name'),
            ('url', 'url'),
            ('username', 'username'),
            ('last_updated', 'last_updated'),
        ),

        field_labels={
            'last_updated': 'Last updated',
        }
    )

    def shared_directly(self, queryset, name, value):
        return get_objects_for_user(self.request.user,
                                    ['view_secret', 'change_secret'],
                                    queryset,
                                    with_superuser=False,
                                    any_perm=True,
                                    use_groups=False)

    def filter_by_group(self, queryset, name, value):
        try:
            if self.request.user.is_superuser:
                group = Group.objects.get(name=value)
            else:
                group = self.request.user.groups.get(name=value)
        except Group.DoesNotExist:
            return queryset

        return get_objects_for_group(group, ['view_secret', 'change_secret'], queryset, any_perm=True)

    @property
    def qs(self):
        parent = super().qs

        if self.request.user.is_superuser:
            return parent
        else:
            return get_objects_for_user(self.request.user, ['view_secret', 'change_secret'], parent, any_perm=True)

    class Meta:
        model = Secret
        fields = ['name', 'username', 'url', 'last_updated']
