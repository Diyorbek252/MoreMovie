"""DRF URL'lar — `/api/v1/auth/...`, `/api/v1/me/...`."""

from django.urls import path

from . import api_v1

urlpatterns = [
    path("auth/csrf/", api_v1.CsrfView.as_view(), name="api-csrf"),
    path("auth/register/", api_v1.RegisterView.as_view(), name="api-register"),
    path("auth/login/", api_v1.LoginView.as_view(), name="api-login"),
    path("auth/logout/", api_v1.LogoutView.as_view(), name="api-logout"),
    path("auth/me/", api_v1.MeView.as_view(), name="api-me"),
    path("me/profile/", api_v1.ProfileUpdateView.as_view(), name="api-profile-update"),
    path("me/watchlist/", api_v1.WatchlistListView.as_view(), name="api-watchlist-list"),
    path("me/favorites/", api_v1.FavoritesListView.as_view(), name="api-favorites-list"),
    path(
        "me/continue-watching/dismiss/",
        api_v1.DismissContinueWatchingView.as_view(),
        name="api-dismiss-continue-watching",
    ),
]
