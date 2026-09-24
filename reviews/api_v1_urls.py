"""DRF URL'lar — `/api/v1/ratings/`, `/api/v1/reviews/`."""

from django.urls import path

from .api_v1 import RateView, ReviewCreateView, ReviewListView

urlpatterns = [
    path("ratings/", RateView.as_view(), name="api-rating"),
    path("reviews/", ReviewListView.as_view(), name="api-review-list"),
    path("reviews/create/", ReviewCreateView.as_view(), name="api-review-create"),
]
