from typing import Any

from actions.models import Action
from actions.utils import create_action
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeDoneView,
    PasswordChangeView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.sites.shortcuts import get_current_site
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, FormView, ListView, UpdateView

from .forms import ProfileEditForm, UserEditForm, UserRegistrationForm
from .models import Contact, Profile
from .tokens import account_activation_token
from .utils import activate_email

User = get_user_model()


class UserRegisterView(FormView):
    template_name = "account/register.html"
    form_class = UserRegistrationForm
    success_url = "/"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self.get_success_url())
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # Create a new user object but avoid saving it yet
        new_user = form.save(commit=False)
        new_user.is_active = False
        # Set the chosen password
        new_user.set_password(form.cleaned_data["password"])
        # Save the User object
        new_user.save()
        # Create the user profile
        Profile.objects.create(user=new_user)
        # Send email verification
        activate_email(self.request, new_user, form.cleaned_data.get("email"))
        # Account creation action
        create_action(new_user, "has created an account")
        return render(
            self.request, "account/register_done.html", {"new_user": new_user}
        )


class UserActivateView(View):

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and account_activation_token.check_token(user, token):
            user.is_active = True
            user.save()
            messages.success(
                request,
                "Thank you for your email confirmation. Now, you can login to your account",
            )
            return redirect("login")
        else:
            messages.error(request, "Activation link is invalid.")

        return redirect("dashboard")


class UserLoginView(SuccessMessageMixin, LoginView):
    redirect_authenticated_user = True
    success_message = "You were successfully logged in."


class UserLogoutView(LogoutView):
    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if request.user.is_authenticated:
            messages.success(
                request, f"{request.user.first_name} successfully logged out"
            )
        else:
            messages.warning(request, "You are not logged in. Please login first!")
            return redirect("login")
        return super().dispatch(request, *args, **kwargs)


class UserPasswordChangeView(SuccessMessageMixin, PasswordChangeView):
    success_message = "Your password was changed successfully."


class UserPasswordChangeDoneView(PasswordChangeDoneView):
    pass


class UserPasswordResetView(PasswordResetView):
    pass


class UserPasswordResetDoneView(PasswordResetDoneView):
    pass


class UserPasswordResetConfirmView(SuccessMessageMixin, PasswordResetConfirmView):
    success_message = "Your password was successfully reset."


class UserPasswordResetCompleteView(PasswordResetCompleteView):
    pass


class DashboardView(LoginRequiredMixin, ListView):
    model = Action
    template_name = "account/dashboard.html"
    context_object_name = "actions"
    paginate_by = 10

    def get_queryset(self) -> QuerySet[Any]:
        queryset = Action.objects.exclude(user=self.request.user)
        following_ids = self.request.user.following.values_list("id", flat=True)
        if following_ids:
            queryset = queryset.filter(user_id__in=following_ids)
        return queryset.select_related("user", "user__profile").prefetch_related(
            "target"
        )

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["section"] = "dashboard"
        return context


class UserEditView(LoginRequiredMixin, UpdateView):
    template_name = "account/edit.html"
    form_class = UserEditForm
    profile_form_class = ProfileEditForm

    def get_object(self):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "profile_form" not in context:
            context["profile_form"] = self.profile_form_class(
                instance=self.request.user.profile
            )
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        user_form = self.get_form()
        profile_form = self.profile_form_class(
            instance=self.object.profile, data=request.POST, files=request.FILES
        )
        if user_form.is_valid() and profile_form.is_valid():
            return self.form_valid(user_form, profile_form)
        else:
            return self.form_invalid(user_form, profile_form)

    def form_valid(self, user_form, profile_form):
        user_form.save()
        profile_form.save()
        messages.success(self.request, "Profile updated successfully")
        return super().form_valid(user_form)

    def form_invalid(self, user_form, profile_form):
        messages.error(self.request, "Error updating your profile")
        return self.render_to_response(
            self.get_context_data(form=user_form, profile_form=profile_form)
        )


class UserListView(LoginRequiredMixin, ListView):
    model = User
    template_name = "account/user/list.html"
    context_object_name = "users"
    paginate_by = 10

    def get_queryset(self):
        return User.objects.filter(is_active=True, is_staff=False)


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = "account/user/detail.html"
    context_object_name = "user"

    def get_queryset(self):
        return User.objects.filter(is_active=True)

    def get_object(self, queryset=None):
        username = self.kwargs.get("username")
        return get_object_or_404(User, username=username, is_active=True)


class UserFollowView(LoginRequiredMixin, View):

    @method_decorator(require_POST)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        user_id = request.POST.get("id")
        action = request.POST.get("action")
        if user_id and action:
            return self.handle_follow_action(request, user_id, action)
        return JsonResponse({"status": "error"})

    def handle_follow_action(self, request, user_id, action):
        try:
            user = User.objects.get(id=user_id)
            if action == "follow":
                return self.follow_user(request, user)
            elif action == "unfollow":
                return self.unfollow_user(request, user)
        except User.DoesNotExist:
            return JsonResponse({"status": "error"})

    def follow_user(self, request, user):
        Contact.objects.get_or_create(user_from=request.user, user_to=user)
        create_action(request.user, "is following", user)
        return JsonResponse({"status": "ok"})

    def unfollow_user(self, request, user):
        Contact.objects.filter(user_from=request.user, user_to=user).delete()
        return JsonResponse({"status": "ok"})
