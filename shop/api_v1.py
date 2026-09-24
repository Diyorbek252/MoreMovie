"""DRF API — do'kon vitrinasi, xarid, xaridlar tarixi.

`purchase_product` dagi biznes-mantiq (atomik tranzaksiya, zaxira
kamayishi, balans debeti) so'z-ma-so'z ko'chirilgan — faqat JSON
parsing/response qatlami DRF'ga o'raladi.
"""

from django.db import transaction
from django.db.models import F, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .models import CinepointTransaction, Order, Product
from .serializers import OrderSerializer, ProductSerializer, PurchaseSerializer
from .services import InsufficientBalanceError, adjust_balance, notify_admins_new_order


class ProductListView(generics.ListAPIView):
    """`GET /api/v1/shop/products/?q=..&affordable=1&sort=..`

    `shop/views.py::ProductListView` bilan bir xil filtr/saralash.
    """

    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

    SORT_OPTIONS = {
        "default": "order",
        "price_asc": "price",
        "price_desc": "-price",
        "newest": "-created_at",
        "az": "name",
    }

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True)
        params = self.request.query_params

        if query := params.get("q", "").strip():
            queryset = queryset.filter(Q(name__icontains=query) | Q(description__icontains=query))

        user = self.request.user
        if params.get("affordable") == "1" and user.is_authenticated:
            queryset = queryset.filter(price__lte=user.profile.balance)

        order_field = self.SORT_OPTIONS.get(params.get("sort", "default"), self.SORT_OPTIONS["default"])
        return queryset.order_by(order_field)


class PurchaseView(APIView):
    """`POST /api/v1/shop/purchase/`  body: {"product": <id>, "quantity": <int>}"""

    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "write"

    def post(self, request):
        serializer = PurchaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = get_object_or_404(
            Product, pk=serializer.validated_data["product"], is_active=True
        )
        quantity = serializer.validated_data["quantity"]
        total_price = product.price * quantity

        with transaction.atomic():
            # Zaxira cheklangan bo'lsa, shartli UPDATE orqali atomik
            # kamaytiramiz — kutilgandan kamrog'i qaytsa, zaxira yetmagan.
            if product.stock is not None:
                rows = Product.objects.filter(pk=product.pk, stock__gte=quantity).update(
                    stock=F("stock") - quantity
                )
                if not rows:
                    return Response({"error": "Mahsulot zaxirasi yetarli emas."}, status=400)

            order = Order.objects.create(
                user=request.user,
                product=product,
                product_name=product.name,
                quantity=quantity,
                price_paid=total_price,
                status=Order.Status.PENDING,
            )

            try:
                adjust_balance(
                    request.user,
                    -total_price,
                    CinepointTransaction.Reason.PURCHASE,
                    note=f"«{product.name}» dan {quantity} dona xaridi",
                    related=order,
                )
            except InsufficientBalanceError:
                transaction.set_rollback(True)
                return Response({"error": "Balansingiz yetarli emas."}, status=400)

        request.user.profile.refresh_from_db(fields=["balance"])
        notify_admins_new_order(order)

        return Response(
            {
                "ok": True,
                "balance": request.user.profile.balance,
                "message": f"«{product.name}» dan {quantity} dona xarid qilindi — buyurtmangiz tez orada yetkaziladi.",
            }
        )


class OrderHistoryListView(generics.ListAPIView):
    """`GET /api/v1/shop/orders/` — «Xaridlarim»."""

    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).select_related("product")
