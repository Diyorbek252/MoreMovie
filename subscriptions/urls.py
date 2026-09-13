"""Obuna — public sahifalar URL lari."""

from django.urls import path

from . import views

app_name = "subscriptions"

urlpatterns = [
    path("obuna/", views.PlanListView.as_view(), name="plan_list"),
    path(
        "obuna/<slug:slug>/rasmiylashtirish/",
        views.SubscriptionRequestView.as_view(),
        name="subscription_request",
    ),
    path("obuna/mening/", views.MySubscriptionView.as_view(), name="my_subscription"),
]
