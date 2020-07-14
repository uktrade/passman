import django_filters

from .models import Secret


class SecretFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains', distinct=True)
    group = django_filters.CharFilter(method='filter_by_group', distinct=True)

    def filter_by_group(self, queryset, name, value):
        return queryset.filter(owner_group__name=value) | queryset.filter(viewer_groups__name=value)

    @property
    def qs(self):
        parent = super().qs

        user_groups = self.request.user.get_permitted_groups()

        return (parent.filter(owner_group__in=user_groups)
               | parent.filter(viewer_groups__in=user_groups)).distinct()

    class Meta:
        model = Secret
        fields = ['name', 'username', 'owner_group', 'viewer_groups']
