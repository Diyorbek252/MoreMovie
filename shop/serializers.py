"""DRF serializerlari — cinepoint do'koni."""

from rest_framework import serializers

from .models import Order, Product


class ProductSerializer(serializers.ModelSerializer):
    is_in_stock = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = ["id", "name", "slug", "description", "image", "price", "stock", "is_in_stock"]


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            "id", "product_name", "quantity", "price_paid", "status",
            "created_at", "delivered_at",
        ]


class PurchaseSerializer(serializers.Serializer):
    """`POST /api/v1/shop/purchase/` — `shop/api.py::purchase_product` DRF ekvivalenti."""

    product = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)
