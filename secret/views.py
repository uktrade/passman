from django.views.generic.edit import CreateView, UpdateView
from django.urls import reverse_lazy

from django_filters.views import FilterView

from .filters import SecretFilter
from .forms import SecretForm
from .models import Secret


class SecretListView(FilterView):
    paginate_by = 100
    filterset_class = SecretFilter
    template_name = 'secret/secret_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({
            'filter_group': self.filterset.data.get('group', None),
            'search_term': self.filterset.data.get('name', None),
        })

        return context


class SecretDetailView(UpdateView):
    model = Secret
    form_class = SecretForm
    success_url = reverse_lazy('secret:list')


class SecretCreateView(CreateView):
    model = Secret
    form_class = SecretForm
    success_url = reverse_lazy('secret:list')
