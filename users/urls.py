"""Autentifikatsiya va foydalanuvchi URL lari."""

from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import api, views

app_name = "users"

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page="core:home"),
        name="logout",
    ),

    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("profile/edit/", views.profile_edit, name="profile_edit"),
    path("watchlist/", views.WatchlistView.as_view(), name="watchlist"),
    path("favorites/", views.FavoritesView.as_view(), name="favorites"),

    # --- AJAX endpointlar ---
    path(
        "api/continue-watching/dismiss/",
        api.dismiss_continue_watching,
        name="api_dismiss_continue_watching",
    ),

    # --- Parolni tiklash (Django ning tayyor view lari + o'z shablonlarimiz) ---
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="users/password_reset.html",
            email_template_name="users/password_reset_email.txt",
            subject_template_name="users/password_reset_subject.txt",
            success_url=reverse_lazy("users:password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "password-reset/sent/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="users/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "password-reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="users/password_reset_confirm.html",
            success_url=reverse_lazy("users:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="users/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
]
