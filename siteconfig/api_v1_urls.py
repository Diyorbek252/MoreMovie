"""DRF URL'lar — `/api/v1/site/...`, `/api/v1/me/notifications/...`."""

from django.urls import path

from . import api_v1

urlpatterns = [
    path("site/settings/", api_v1.SiteSettingsView.as_view(), name="api-site-settings"),
    path("site/banners/", api_v1.BannerListView.as_view(), name="api-site-banners"),
    path("me/notifications/", api_v1.NotificationListView.as_view(), name="api-notifications"),
    path(
        "me/notifications/<int:pk>/read/",
        api_v1.NotificationMarkReadView.as_view(),
        name="api-notification-read",
    ),
    path(
        "me/notifications/read-all/",
        api_v1.NotificationMarkAllReadView.as_view(),
        name="api-notifications-read-all",
    ),
]
