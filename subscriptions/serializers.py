"""DRF serializerlari — obuna rejalari va so'rovlar."""

from rest_framework import serializers

from .models import Plan, PlanPrice, Subscription


class PlanPriceSerializer(serializers.ModelSerializer):
    monthly_equivalent = serializers.ReadOnlyField()
    discount_percent = serializers.ReadOnlyField()

    class Meta:
        model = PlanPrice
        fields = [
            "id", "label", "duration_days", "price", "old_price",
            "monthly_equivalent", "discount_percent",
        ]


class PlanSerializer(serializers.ModelSerializer):
    feature_list = serializers.ReadOnlyField()
    prices = PlanPriceSerializer(many=True, read_only=True)
    cheapest_price = serializers.SerializerMethodField()

    class Meta:
        model = Plan
        fields = [
            "id", "name", "slug", "tagline", "description", "feature_list",
            "level", "allows_premium_movies", "has_badge", "is_ad_free",
            "is_highlighted", "prices", "cheapest_price",
        ]

    def get_cheapest_price(self, obj):
        price = obj.cheapest_price
        return PlanPriceSerializer(price).data if price else None


class SubscriptionSerializer(serializers.ModelSerializer):
    """`GET /api/v1/subscriptions/me/` — «Mening obunam» ro'yxati."""

    is_currently_active = serializers.ReadOnlyField()
    days_left = serializers.ReadOnlyField()
    percent_left = serializers.ReadOnlyField()

    class Meta:
        model = Subscription
        fields = [
            "id", "plan_name", "duration_days", "price_paid", "status",
            "payment_note", "admin_note", "starts_at", "ends_at",
            "is_currently_active", "days_left", "percent_left", "created_at",
        ]


class SubscriptionRequestSerializer(serializers.ModelSerializer):
    """`POST /api/v1/subscriptions/plans/<slug>/request/` uchun yozish
    qismi — `SubscriptionRequestForm` bilan bir xil maydonlar."""

    price = serializers.PrimaryKeyRelatedField(queryset=PlanPrice.objects.all())

    class Meta:
        model = Subscription
        fields = ["price", "payment_note", "payment_receipt"]
