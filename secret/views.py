from django.contrib.auth.models import Group
from django.contrib import messages
from django.views.generic import FormView, TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters

from django_filters.views import FilterView
from guardian.shortcuts import assign_perm, get_groups_with_perms, get_users_with_perms, get_perms

from audit.models import Actions, Audit
from user.models import User
from .filters import SecretFilter
from .forms import EDIT_SECRET_PERMISSION, VIEW_SECRET_PERMISSION, PERMISSION_CHOICES
from .forms import SecretCreateForm, SecretUpdateForm, SecretPermissionsForm
from .models import Secret


class SecretListView(FilterView):
    paginate_by = 10
    filterset_class = SecretFilter
    template_name = 'secret/secret_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({
            'filter_group': self.filterset.data.get('group', None),
            'search_term': self.filterset.data.get('name', None),
        })

        return context


@method_decorator(sensitive_post_parameters('password', 'details'), name='dispatch')
class SecretCreateView(CreateView):
    model = Secret
    form_class = SecretCreateForm
    ordering = ['name']

    def form_valid(self, form):
        messages.add_message(self.request, messages.INFO, 'Password created')

        http_response = super().form_valid(form)

        # give the user edit permissions
        assign_perm(EDIT_SECRET_PERMISSION, self.request.user, self.object)
        assign_perm(VIEW_SECRET_PERMISSION, self.request.user, self.object)

        Audit.objects.create(user=self.request.user, secret=self.object, action=Actions.created_secret)
        return http_response


@method_decorator(sensitive_post_parameters('password', 'details'),  name='dispatch')
class SecretDetailView(UpdateView):
    model = Secret
    form_class = SecretUpdateForm

    def get(self, request, *args, **kwargs):
        Audit.objects.create(user=self.request.user, secret=self.get_object(), action=Actions.viewed_secret)
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        messages.add_message(self.request, messages.INFO, 'Password updated')
        Audit.objects.create(user=self.request.user, secret=self.get_object(), action=Actions.updated_secret)
        return super().form_valid(form)

    def get_success_url(self):
        if 'save' in self.request.POST:
            self.success_url = reverse('secret:list')

        return super().get_success_url()

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context['pk'] = self.kwargs['pk']
        context['tab'] = 'view'

        return context


class SecretAuditView(TemplateView):
    template_name = 'secret/secret_audit.html'

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context['audit_info'] = Audit.objects.filter(secret__pk=kwargs['pk']).order_by('-timestamp')
        context['tab'] = 'audit'

        return context


class SecretPermissionsView(FormView):
    template_name = 'secret/permissions.html'
    form_class = SecretPermissionsForm

    def get_success_url(self):
        return reverse('secret:permissions', kwargs=dict(pk=self.kwargs['pk']))

    def form_valid(self, form):

        secret = Secret.objects.get(pk=self.kwargs['pk'])

        http_response = super().form_valid(form)

        assignee = form.cleaned_data['user'] or form.cleaned_data['group']

        # if the user has been granted change permissions also give them view permission
        if form.cleaned_data['permission'] == EDIT_SECRET_PERMISSION:
            assign_perm(VIEW_SECRET_PERMISSION, assignee, secret)

        assign_perm(form.cleaned_data['permission'], assignee, secret)

        messages.add_message(self.request, messages.INFO, 'Permission added')
        return http_response

    def get_context_data(self, **kwargs):
        perm_display = dict(PERMISSION_CHOICES)

        def _flatten_perms(items):
            """change `{user: [perm1, perm2]}` to `[(user, perm1), (user, perm2)]]` we're also removing additional
            perms i.e. superusers have additional perms: add_secret, delete_secret which aren't relevant"""

            return [
                (user, (perm, perm_display.get(perm, perm))) for user, perms in items.items() for perm in perms
                if perm in [EDIT_SECRET_PERMISSION, VIEW_SECRET_PERMISSION]
            ]

        context = super().get_context_data(**kwargs)

        pk = context['pk'] = self.kwargs['pk']
        context['tab'] = 'permissions'

        secret = Secret.objects.get(pk=pk)
        context['users'] = _flatten_perms(get_users_with_perms(
            secret, attach_perms=True,
            only_with_perms_in=[EDIT_SECRET_PERMISSION, VIEW_SECRET_PERMISSION]
        ))
        context['groups'] = _flatten_perms(get_groups_with_perms(secret, attach_perms=True))

        return context


class SecretPermissionsDeleteView(DetailView):
    model = Secret
    template_name = 'secret/confirm-delete.html'

    def _get_params(self, request):
        user_id = request.GET.get('user', None)
        group_name = request.GET.get('group', None)
        permission = request.GET.get('permission', None)

        user, group = None, None

        if user_id:
            user = User.objects.get(email=user_id)
        elif group_name:
            group = Group.objects.get(name=group_name)
        else:
            raise Exception('No user or group set')

        if permission not in PERMISSION_CHOICES:
            raise Exception('Invalid permission')

        return user, group, permission

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        pass

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context['pk'] = self.kwargs['pk']
        context['tab'] = 'permissions'

        return context
