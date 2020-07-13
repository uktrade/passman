from django.views.generic.edit import CreateView, UpdateView
from django.urls import reverse_lazy

from django_filters.views import FilterView

from audit.models import Actions, Audit
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

    def get(self, request, *args, **kwargs):
        Audit.objects.create(user=self.request.user, secret=self.get_object(), action=Actions.viewed_secret)
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        Audit.objects.create(user=self.request.user, secret=self.get_object(), action=Actions.updated_secret)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context['audit_info'] = Audit.objects.filter(secret=self.get_object()).order_by('-timestamp')

        return context


class SecretCreateView(CreateView):
    model = Secret
    form_class = SecretForm
    success_url = reverse_lazy('secret:list')

    def form_valid(self, form):
        response = super().form_valid(form)
        Audit.objects.create(user=self.request.user, secret=self.object, action=Actions.created_secret)
        return response

