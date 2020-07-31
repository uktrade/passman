from django.conf import settings
from django.contrib import messages
from django.views.generic import FormView, TemplateView
from django.views.generic.base import ContextMixin
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.urls import reverse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters

from django_filters.views import FilterView
from guardian.shortcuts import (
    assign_perm,
    get_groups_with_perms,
    get_users_with_perms,
    remove_perm,
)
from guardian.decorators import permission_required_or_403
from django_otp.decorators import otp_required

from audit.models import Actions, Audit, create_audit_event
from .filters import SecretFilter
from .forms import (
    EDIT_SECRET_PERMISSION,
    VIEW_SECRET_PERMISSION,
    PERMISSION_CHOICES,
    SecretCreateForm,
    SecretUpdateForm,
    SecretPermissionsForm,
    SecretGroupPermissionsForm,
    SecretUserPermissionsForm,
)
from .models import Secret


class SecretListView(FilterView):
    paginate_by = settings.SECRET_PAGINATION_ITEMS_PER_PAGE
    filterset_class = SecretFilter
    template_name = "secret/secret_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        filter_group = self.filterset.data.get(
            "group", "__me" if "me" in self.filterset.data else None
        )

        context.update(
            {"filter_group": filter_group, "search_term": self.filterset.data.get("name", None),}
        )

        return context


@method_decorator(sensitive_post_parameters("password", "details"), name="dispatch")
@method_decorator(otp_required, name="dispatch")
class SecretCreateView(CreateView):
    model = Secret
    form_class = SecretCreateForm
    ordering = ["name"]

    def form_valid(self, form):
        messages.info(self.request, "Secret created")

        http_response = super().form_valid(form)

        # give the user edit permissions
        assign_perm(EDIT_SECRET_PERMISSION, self.request.user, self.object)
        assign_perm(VIEW_SECRET_PERMISSION, self.request.user, self.object)

        create_audit_event(self.request.user, Actions.created_secret, secret=self.object)
        return http_response


@method_decorator(sensitive_post_parameters("password", "details"), name="dispatch")
@method_decorator(otp_required, name="dispatch")
@method_decorator(
    permission_required_or_403("secret.change_secret", (Secret, "pk", "pk")), name="post",
)
@method_decorator(
    permission_required_or_403("secret.view_secret", (Secret, "pk", "pk")), name="get"
)
class SecretDetailView(UpdateView):
    model = Secret
    form_class = SecretUpdateForm

    def get(self, request, *args, **kwargs):
        create_audit_event(
            self.request.user, Actions.viewed_secret, secret=self.get_object(), report_once=True,
        )
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        messages.info(self.request, "Secret updated")
        create_audit_event(self.request.user, Actions.updated_secret, secret=self.get_object())

        return super().form_valid(form)

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context["pk"] = self.kwargs["pk"]
        context["tab"] = "view"

        return context


@method_decorator(otp_required, name="dispatch")
@method_decorator(
    permission_required_or_403("secret.view_secret", (Secret, "pk", "pk")), name="dispatch",
)
class SecretAuditView(TemplateView):
    template_name = "secret/secret_audit.html"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context["audit_info"] = Audit.objects.filter(secret__pk=kwargs["pk"]).order_by("-timestamp")
        context["tab"] = "audit"

        return context


@method_decorator(otp_required, name="dispatch")
@method_decorator(
    permission_required_or_403("secret.change_secret", (Secret, "pk", "pk")), name="post",
)
@method_decorator(
    permission_required_or_403("secret.change_secret", (Secret, "pk", "pk")), name="get"
)
class SecretPermissionsDeleteView(DetailView):
    model = Secret
    template_name = "secret/confirm-delete.html"
    object = None

    def redirect_to_permissions_list(self, *message_params):
        messages.add_message(self.request, *message_params)
        return redirect("secret:permissions", **self.kwargs)

    def get(self, request, *args, **kwargs):
        form = SecretPermissionsForm(request.GET)
        if not form.is_valid():
            return self.redirect_to_permissions_list(messages.ERROR, "Invalid parameters")

        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        context.update(form.cleaned_data)
        context["permission_display"] = dict(PERMISSION_CHOICES)[context["permission"]]
        context["form"] = form

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):

        form = SecretPermissionsForm(request.POST)
        if not form.is_valid():
            return self.redirect_to_permissions_list(messages.ERROR, "Invalid parameters")

        object = form.cleaned_data["user"] or form.cleaned_data["group"]

        remove_perm(form.cleaned_data["permission"], object, self.get_object())

        create_audit_event(
            self.request.user,
            Actions.remove_permission,
            secret=self.get_object(),
            description=f'{form.cleaned_data["permission"]} removed for {object}',
        )

        return self.redirect_to_permissions_list(messages.INFO, "Permission removed")

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context["pk"] = self.kwargs["pk"]
        context["tab"] = "permissions"

        return context


@method_decorator(otp_required, name="dispatch")
@method_decorator(
    permission_required_or_403("secret.change_secret", (Secret, "pk", "pk")), name="post",
)
@method_decorator(
    permission_required_or_403("secret.view_secret", (Secret, "pk", "pk")), name="get"
)
class SecretPermissionsView(FormView):
    template_name = "secret/permissions.html"

    def get_success_url(self):
        return reverse("secret:permissions", kwargs=dict(pk=self.kwargs["pk"]))

    def get_form_class(self):
        """Return the correct form based the key in `request.POST`; if the page is not posted, then we return
        a single form to appease the existing FormView logic."""
        if self.request.POST.get("group"):
            return SecretGroupPermissionsForm
        else:
            return SecretUserPermissionsForm

    def form_valid(self, form):

        secret = Secret.objects.get(pk=self.kwargs["pk"])

        http_response = super().form_valid(form)
        assignee = form.cleaned_data.get("user", form.cleaned_data.get("group"))

        assert assignee

        # if the user has been granted change permissions also give them view permission
        if form.cleaned_data["permission"] == EDIT_SECRET_PERMISSION:
            assign_perm(VIEW_SECRET_PERMISSION, assignee, secret)

        assign_perm(form.cleaned_data["permission"], assignee, secret)

        secret = Secret.objects.get(pk=self.kwargs["pk"])

        create_audit_event(
            self.request.user,
            Actions.add_permission,
            secret=secret,
            description=f'{form.cleaned_data["permission"]} granted to {assignee}',
        )

        messages.info(self.request, "Permission added")
        return http_response

    def get_context_data(self, **kwargs):
        perm_display = dict(PERMISSION_CHOICES)

        def _flatten_perms(items):
            """change `{user: [perm1, perm2]}` to `[(user, perm1), (user, perm2)]]` we're also removing additional
            perms i.e. superusers have additional perms: add_secret, delete_secret which aren't relevant, so they
            are skipped. We also provide a display-friendly perm-name."""

            return [
                (user, (perm, perm_display.get(perm, perm)))
                for user, perms in items.items()
                for perm in perms
                if perm in [EDIT_SECRET_PERMISSION, VIEW_SECRET_PERMISSION]
            ]

        context = ContextMixin.get_context_data(self, **kwargs)

        if self.request.method == "POST":
            if self.request.POST.get("group"):
                context["group_form"] = self.get_form()
            else:
                context["user_form"] = self.get_form()

        context.setdefault("group_form", SecretGroupPermissionsForm())
        context.setdefault("user_form", SecretUserPermissionsForm())

        pk = context["pk"] = self.kwargs["pk"]
        context["tab"] = "permissions"

        secret = Secret.objects.get(pk=pk)

        context["users"] = _flatten_perms(
            get_users_with_perms(
                secret,
                attach_perms=True,
                only_with_perms_in=[EDIT_SECRET_PERMISSION, VIEW_SECRET_PERMISSION],
            )
        )
        context["groups"] = _flatten_perms(get_groups_with_perms(secret, attach_perms=True))

        return context
