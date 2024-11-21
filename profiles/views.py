import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegisterForm, ProfileUpdateForm, UserUpdateForm
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth import logout
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from django.contrib.auth.models import User
from .tokens import account_activation_token
import logging

logger = logging.getLogger(__name__)


def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Deactivate account till it is confirmed
            user.save()

            current_site = get_current_site(request)
            mail_subject = "Activate your account"
            message = render_to_string(
                "profiles/acc_active_email.html",
                {
                    "user": user,
                    "domain": current_site.domain,
                    "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                    "token": account_activation_token.make_token(user),
                },
            )
            email = EmailMessage(mail_subject, message, to=[user.email])
            email.send()
            messages.success(
                request,
                "Please confirm your email address to complete the registration",
            )
            return redirect("login")
    else:
        form = UserRegisterForm()
    return render(request, "profiles/register.html", {"form": form})


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(
            request, "Thank you for confirming your email. You can now login."
        )
        return redirect("login")
    else:
        messages.error(request, "Activation link is invalid!")
        return redirect("register")


def password_reset_request(request):
    if request.method == "POST":
        email = request.POST.get("email", "")
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            current_site = get_current_site(request)
            mail_subject = "Reset your password"
            message = render_to_string(
                "profiles/password_reset_email.html",
                {
                    "user": user,
                    "domain": current_site.domain,
                    "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                    "token": account_activation_token.make_token(user),
                },
            )
            email = EmailMessage(mail_subject, message, to=[user.email])
            email.send()
            messages.success(request, "Password reset email has been sent.")
            return redirect("login")
        messages.error(request, "No user found with that email address.")
    return render(request, "profiles/password_reset.html")


@login_required
def profile(request):
    """View for rendering the profile view template"""
    context = {
        "profile": request.user.profile
    }
    return render(request, "profiles/profile_view.html", context)


@login_required
def edit_profile(request):
    """View for rendering the profile edit template"""
    u_form = UserUpdateForm(instance=request.user)
    p_form = ProfileUpdateForm(instance=request.user.profile)
    context = {
        "u_form": u_form,
        "p_form": p_form,
        "profile": request.user.profile
    }
    return render(request, "profiles/profile_edit.html", context)


@login_required
@require_http_methods(["POST"])
def update_profile(request):
    """API endpoint for updating profile details"""
    try:
        data = json.loads(request.POST.get("data", "{}"))
        profile = request.user.profile
        user = request.user

        # Handle user data updates
        if "username" in data:
            u_form = UserUpdateForm(data, instance=user)
            if u_form.is_valid():
                u_form.save()
            else:
                return JsonResponse(
                    {"status": "error", "errors": u_form.errors}, status=400
                )

        # Handle profile data updates
        profile_data = {
            "student_id": data.get("student_id", profile.student_id),
            "course": data.get("course", profile.course),
            "year_of_study": data.get("year_of_study", profile.year_of_study),
            "bio": data.get("bio", profile.bio),
            "campus": data.get("campus", profile.campus),
            "gender": data.get("gender", profile.gender),
            "date_of_birth": data.get("date_of_birth", profile.date_of_birth),
        }

        p_form = ProfileUpdateForm(profile_data, instance=profile)
        if p_form.is_valid():
            p_form.save()

            # Handle profile picture separately
            if "profile_pic" in request.FILES:
                profile_pic = request.FILES["profile_pic"]
                path = default_storage.save(
                    f"profile_pics/{user.username}_{profile_pic.name}",
                    ContentFile(profile_pic.read()),
                )
                profile.profile_pic = path
                profile.save()

            return JsonResponse(
                {
                    "status": "success",
                    "message": "Profile updated successfully",
                    "data": {
                        "username": user.username,
                        "email": user.email,
                        "profile_pic_url": profile.get_avatar_url(),
                        **profile_data,
                    },
                }
            )
        else:
            return JsonResponse(
                {"status": "error", "errors": p_form.errors}, status=400
            )

    except json.JSONDecodeError:
        return JsonResponse(
            {"status": "error", "message": "Invalid JSON data"}, status=400
        )
    except Exception as e:
        logging.error("An error occurred while updating profile: %s", str(e))
        return JsonResponse(
            {"status": "error", "message": "An internal error has occurred."},
            status=500,
        )


@login_required
@require_http_methods(["POST"])
def delete_account(request):
    """API endpoint for account deletion"""
    try:
        user = request.user
        logout(request)
        user.delete()
        return JsonResponse(
            {"status": "success", "message": "Account deleted successfully"}
        )
    except Exception as e:

        logger.error("An error occurred in update_profile: %s", str(e))
        return JsonResponse(
            {"status": "error", "message": "An internal error has occurred."},
            status=500,
        )
