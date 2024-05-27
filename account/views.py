from typing import Any

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import (LoginView, LogoutView,
                                       PasswordChangeDoneView,
                                       PasswordChangeView,
                                       PasswordResetCompleteView,
                                       PasswordResetConfirmView,
                                       PasswordResetDoneView,
                                       PasswordResetView)
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.http import require_POST

from actions.models import Action
from actions.utils import create_action

from .forms import ProfileEditForm, UserEditForm, UserRegistrationForm
from .models import Contact, Profile
from .tokens import account_activation_token


class UserLoginView(SuccessMessageMixin, LoginView):
    redirect_authenticated_user=True
    success_message = 'You were successfully logged in.'
    
class UserLogoutView(LogoutView):
    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if request.user.is_authenticated:
            messages.success(request, f'{request.user.first_name} successfully logged out')
        else:
            messages.warning(request, 'You are not logged in. Please login first!')
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

class UserPasswordChangeView(SuccessMessageMixin, PasswordChangeView):
    success_message = 'Your password was changed successfully.'

class UserPasswordChangeDoneView(PasswordChangeDoneView):
    pass

class UserPasswordResetView(PasswordResetView):
    pass

class UserPasswordResetDoneView(PasswordResetDoneView):
    pass

class UserPasswordResetConfirmView(SuccessMessageMixin, PasswordResetConfirmView):
    success_message = 'Your password was successfully reset.'

class UserPasswordResetCompleteView(PasswordResetCompleteView):
    pass

@login_required
def dashboard(request):
    # Display all actions by default
    actions = Action.objects.exclude(user=request.user)
    following_ids = request.user.following.values_list("id", flat=True)
    if following_ids:
        # If user is following others, retrieve only their actions
        actions = actions.filter(user_id__in=following_ids)
    actions = actions.select_related("user", "user__profile").prefetch_related(
        "target"
    )[:10]
    return render(
        request, "account/dashboard.html", {"section": "dashboard", "actions": actions}
    )


def register(request):
    if request.user.is_authenticated:
        return redirect("/")
    if request.method == "POST":
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            # Create a new user object but avoid saving it yet
            new_user = user_form.save(commit=False)
            new_user.is_active = False
            # Set the chosen password
            new_user.set_password(user_form.cleaned_data["password"])
            # Save the User object
            new_user.save()
            # Create the user profile
            Profile.objects.create(user=new_user)
            # Send email verification 
            # activate_email(request, new_user, user_form.cleaned_data.get("email"))
            # Account creation action
            create_action(new_user, "has created an account")
            return render(request, "account/register_done.html", {"new_user": new_user})
    else:
        user_form = UserRegistrationForm()
    return render(request, "account/register.html", {"user_form": user_form})


def activate_email(request, user, to_email):
    mail_subject = "Activate your user account"
    message = render_to_string(
        "account/email_verification.html",
        {
            "user": user.username,
            "domain": get_current_site(request).domain,
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": account_activation_token.make_token(user),
            "protocol": "https" if request.is_secure() else "http",
        },
    )
    email = EmailMessage(mail_subject, message, to=[to_email])
    if email.send():
        messages.success(
            request,
            f"Dear <b>{user}</b>, please go to you email <b>{to_email}</b> inbox and click on \
            received activation link to confirm and complete the registration. <b>Note:</b> Check your spam folder.",
        )
    else:
        messages.error(
            request,
            f"Problem sending confirmation email to {to_email}, check if you typed it correctly.",
        )


def activate(request, uidb64, token):
    user = get_user_model()
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
        messages.error(request, "Activation link is invalid!")

    return redirect("dashboard")


@login_required
def edit(request):
    if request.method == "POST":
        user_form = UserEditForm(instance=request.user, data=request.POST)
        profile_form = ProfileEditForm(
            instance=request.user.profile, data=request.POST, files=request.FILES
        )
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Profile updated " "successfully")
        else:
            messages.error(request, "Error updating your profile")
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=request.user.profile)
    return render(
        request,
        "account/edit.html",
        {"user_form": user_form, "profile_form": profile_form},
    )


@login_required
def user_list(request):
    users = User.objects.filter(is_active=True, is_staff=False)
    return render(
        request, "account/user/list.html", {"section": "people", "users": users}
    )


@login_required
def user_detail(request, username):
    user = get_object_or_404(User, username=username, is_active=True)
    return render(
        request, "account/user/detail.html", {"section": "people", "user": user}
    )


@require_POST
@login_required
def user_follow(request):
    user_id = request.POST.get("id")
    action = request.POST.get("action")
    if user_id and action:
        try:
            user = User.objects.get(id=user_id)
            if action == "follow":
                Contact.objects.get_or_create(user_from=request.user, user_to=user)
                create_action(request.user, "is following", user)
            else:
                Contact.objects.filter(user_from=request.user, user_to=user).delete()
            return JsonResponse({"status": "ok"})
        except User.DoesNotExist:
            return JsonResponse({"status": "error"})
    return JsonResponse({"status": "error"})
