"""DRF URL'lar — `/api/v1/shop/...`."""

from django.urls import path

from . import api_v1

urlpatterns = [
    path("shop/products/", api_v1.ProductListView.as_view(), name="api-shop-products"),
    path("shop/purchase/", api_v1.PurchaseView.as_view(), name="api-shop-purchase"),
    path("shop/orders/", api_v1.OrderHistoryListView.as_view(), name="api-shop-orders"),
]
