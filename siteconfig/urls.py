"""Foydalanuvchi bildirishnomalari uchun public AJAX endpointlar.

Diqqat: bu ilovaning DASHBOARD (admin) sahifalari `dashboard/urls.py` da
joylashgan — bu yerda faqat oddiy foydalanuvchining o'ziga tegishli
bildirishnomalarini o'qish/belgilash uchun ochiq endpointlar bor.
"""

from django.urls import path

from . import api

app_name = "siteconfig"

urlpatterns = [
    path("api/notifications/", api.recent_notifications, name="api_notifications"),
    path(
        "api/notifications/<int:pk>/read/",
        api.mark_read, name="api_notification_read",
    ),
    path(
        "api/notifications/read-all/",
        api.mark_all_read, name="api_notifications_read_all",
    ),
]
