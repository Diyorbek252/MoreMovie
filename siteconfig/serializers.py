"""DRF serializerlari — sayt sozlamalari, bannerlar, bildirishnomalar."""

from rest_framework import serializers

from .models import Banner, NotificationRecipient, SiteSettings


class SiteSettingsSerializer(serializers.ModelSerializer):
    """`GET /api/v1/site/settings/` — navbar/footer/brend uchun.

    `siteconfig.context_processors.site_settings` bilan bir xil manba
    (`SiteSettings.load()`, keshlangan singleton).
    """

    class Meta:
        model = SiteSettings
        fields = [
            "site_name", "logo", "favicon", "site_description",
            "contact_email", "telegram", "youtube", "instagram", "facebook",
            "copyright_text", "seo_title", "seo_description", "seo_keywords",
            "google_analytics_id", "maintenance_mode", "maintenance_message",
            "payment_card_number", "payment_card_holder", "payment_instructions",
        ]


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = ["id", "title", "image", "link", "position"]


class NotificationSerializer(serializers.Serializer):
    """`siteconfig/api.py::_serialize` bilan bir xil shakl."""

    id = serializers.IntegerField()
    title = serializers.CharField(source="notification.title")
    message = serializers.CharField(source="notification.message")
    type = serializers.CharField(source="notification.notification_type")
    link = serializers.CharField(source="notification.link")
    image = serializers.SerializerMethodField()
    is_read = serializers.BooleanField()
    created_at = serializers.DateTimeField()

    def get_image(self, obj: NotificationRecipient):
        return obj.notification.image.url if obj.notification.image else ""
