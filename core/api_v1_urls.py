"""DRF URL'lar — `/api/v1/home/`, `/api/v1/catalog/`, `/api/v1/contact/`."""

from django.urls import path

from . import api_v1

urlpatterns = [
    path("home/", api_v1.HomeAPIView.as_view(), name="api-home"),
    path("catalog/", api_v1.CatalogAPIView.as_view(), name="api-catalog"),
    path("contact/", api_v1.ContactView.as_view(), name="api-contact"),
]
