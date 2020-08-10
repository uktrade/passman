import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import Group
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
)
from guardian.decorators import permission_required_or_403
from django_otp.decorators import otp_required

from audit.models import Actions, Audit, create_audit_event
from user.models import User
from .filters import SecretFilter
from .forms import (
    EDIT_SECRET_PERMISSION,
    VIEW_SECRET_PERMISSION,
    SecretCreateForm,
    SecretUpdateForm,
    SecretPermissionsForm,
    SecretGroupPermissionsForm,
    SecretUserPermissionsForm,
)
from .models import Secret


logger = logging.getLogger(__name__)


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

    def get_target_object(self):

        request_dict = self.request.POST if self.request.method == "POST" else self.request.GET

        user_pk = request_dict.get("user", None)
        group_pk = request_dict.get("group", None)

        user, group = None, None

        if user_pk:
            try:
                user = User.objects.get(pk=int(user_pk))
            except (User.DoesNotExist, TypeError):
                pass
            return "user", user

        if group_pk:
            try:
                group = Group.objects.get(pk=int(group_pk))
            except (Group.DoesNotExist, TypeError):
                pass
            return "group", group

        return None, None

    def redirect_to_permissions_list(self, *message_params):
        messages.add_message(self.request, *message_params)
        return redirect("secret:permissions", **self.kwargs)

    def get(self, request, *args, **kwargs):
        object_type, target = self.get_target_object()

        if not target:
            return self.redirect_to_permissions_list(messages.ERROR, "Invalid parameters")

        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        context.update({"target": target, "object_type": object_type})

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):

        object_type, target = self.get_target_object()

        if not target:
            return self.redirect_to_permissions_list(messages.ERROR, "Invalid parameters")

        self.get_object().remove_permissions(target)

        create_audit_event(
            self.request.user,
            Actions.remove_permission,
            secret=self.get_object(),
            description=f"Access removed for {target}",
        )

        return self.redirect_to_permissions_list(messages.INFO, f"Access removed for {target}")

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

        target = form.cleaned_data.get("user", form.cleaned_data.get("group"))
        assert target

        secret.set_permission(target, form.cleaned_data["permission"])

        create_audit_event(
            self.request.user,
            Actions.add_permission,
            secret=secret,
            description=f'Permission level to set {form.cleaned_data["permission"]} for {target}',
        )

        messages.info(self.request, f"Permissions updated for {target}")

        return http_response

    def get_context_data(self, **kwargs):

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

        users = get_users_with_perms(
            secret,
            attach_perms=True,
            with_superusers=False,
            with_group_users=False,
            only_with_perms_in=[EDIT_SECRET_PERMISSION, VIEW_SECRET_PERMISSION],
        )

        def select_perm(perms):
            return "change_secret" if "change_secret" in perms else "view_secret"

        context["users"] = [
            {
                "user": user,
                "form": SecretPermissionsForm(
                    update_permission=True,
                    initial={"user": user, "permission": select_perm(perms)},
                ),
            }
            for user, perms in users.items()
        ]
        groups = get_groups_with_perms(secret, attach_perms=True)

        context["groups"] = [
            {
                "group": group,
                "form": SecretPermissionsForm(
                    update_permission=True,
                    initial={"group": group, "permission": select_perm(perms)},
                ),
            }
            for group, perms in groups.items()
        ]

        return context
