"""DRF API — obuna rejalari, so'rov yuborish, "mening obunam"."""

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Plan, PlanPrice, Subscription
from .serializers import PlanSerializer, SubscriptionRequestSerializer, SubscriptionSerializer
from .services import notify_admins_new_subscription


class PlanListView(generics.ListAPIView):
    """`GET /api/v1/subscriptions/plans/` — narxlar sahifasi."""

    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Plan.objects.filter(is_active=True).prefetch_related("prices")


class SubscriptionRequestView(APIView):
    """`POST /api/v1/subscriptions/plans/<slug>/request/` (multipart)

    Body: {"price": <PlanPrice id>, "payment_note": "...", "payment_receipt": <fayl>}
    `subscriptions/views.py::SubscriptionRequestView.form_valid` bilan bir
    xil mantiq — narx snapshot sifatida saqlanadi, admin bildirishnoma oladi.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug):
        plan = generics.get_object_or_404(Plan, slug=slug, is_active=True)
        serializer = SubscriptionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        price = serializer.validated_data["price"]
        if price.plan_id != plan.pk or not price.is_active:
            return Response(
                {"price": ["Bu narx tanlangan rejaga tegishli emas."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        subscription = Subscription.objects.create(
            user=request.user,
            plan=plan,
            plan_name=plan.name,
            duration_days=price.duration_days,
            price_paid=price.price,
            status=Subscription.Status.PENDING,
            payment_note=serializer.validated_data.get("payment_note", ""),
            payment_receipt=serializer.validated_data.get("payment_receipt"),
        )

        notify_admins_new_subscription(subscription)
        return Response(SubscriptionSerializer(subscription).data, status=status.HTTP_201_CREATED)


class MySubscriptionListView(generics.ListAPIView):
    """`GET /api/v1/subscriptions/me/`"""

    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user).select_related("plan")
