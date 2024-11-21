from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("register/", views.register, name="register"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="profiles/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("api/profile/update/", views.update_profile, name="api_update_profile"),
    path("api/profile/delete/", views.delete_account, name="api_delete_account"),
    # Email Verification URLs
    path("activate/<uidb64>/<token>/", views.activate, name="activate"),
    # Password Reset URLs
    path("password-reset/", views.password_reset_request, name="password_reset"),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="profiles/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "password-reset-confirm/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="profiles/password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    path(
        "password-reset-complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="profiles/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
]
