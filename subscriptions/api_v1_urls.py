"""DRF URL'lar — `/api/v1/subscriptions/...`."""

from django.urls import path

from . import api_v1

urlpatterns = [
    path("subscriptions/plans/", api_v1.PlanListView.as_view(), name="api-plan-list"),
    path(
        "subscriptions/plans/<slug:slug>/request/",
        api_v1.SubscriptionRequestView.as_view(),
        name="api-subscription-request",
    ),
    path("subscriptions/me/", api_v1.MySubscriptionListView.as_view(), name="api-subscription-me"),
]
