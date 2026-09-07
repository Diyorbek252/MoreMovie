"""Do'kon URL lari — public sahifalar va AJAX xarid endpointi."""

from django.urls import path

from . import api, views

app_name = "shop"

urlpatterns = [
    path("shop/", views.ProductListView.as_view(), name="product_list"),
    path("shop/purchases/", views.OrderHistoryView.as_view(), name="order_history"),
    path("api/shop/purchase/", api.purchase_product, name="api_purchase"),
]
