"""DRF API — sayt sozlamalari, bannerlar, bildirishnomalar."""

from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Banner, NotificationRecipient, SiteSettings
from .serializers import BannerSerializer, NotificationSerializer, SiteSettingsSerializer

RECENT_LIMIT = 15


class SiteSettingsView(APIView):
    """`GET /api/v1/site/settings/`"""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(SiteSettingsSerializer(SiteSettings.load()).data)


class BannerListView(generics.ListAPIView):
    """`GET /api/v1/site/banners/?position=homepage_hero`"""

    serializer_class = BannerSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Banner.objects.running(position=self.request.query_params.get("position"))


class NotificationListView(APIView):
    """`GET /api/v1/me/notifications/` — `siteconfig/api.py::recent_notifications` ekvivalenti."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        recipients = (
            NotificationRecipient.objects.filter(user=request.user)
            .select_related("notification")
            .order_by("-created_at")[:RECENT_LIMIT]
        )
        unread_count = NotificationRecipient.objects.filter(
            user=request.user, is_read=False
        ).count()
        return Response(
            {
                "results": NotificationSerializer(recipients, many=True).data,
                "unread_count": unread_count,
            }
        )


class NotificationMarkReadView(APIView):
    """`POST /api/v1/me/notifications/<id>/read/`"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        recipient = generics.get_object_or_404(
            NotificationRecipient, pk=pk, user=request.user
        )
        if not recipient.is_read:
            recipient.is_read = True
            recipient.read_at = timezone.now()
            recipient.save(update_fields=["is_read", "read_at"])
        return Response(
            {
                "marked": True,
                "unread_count": NotificationRecipient.objects.filter(
                    user=request.user, is_read=False
                ).count(),
            }
        )


class NotificationMarkAllReadView(APIView):
    """`POST /api/v1/me/notifications/read-all/`"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        NotificationRecipient.objects.filter(user=request.user, is_read=False).update(
            is_read=True, read_at=timezone.now()
        )
        return Response({"marked": True, "unread_count": 0})
