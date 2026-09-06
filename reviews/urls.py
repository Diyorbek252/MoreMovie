"""Reyting va sharh AJAX endpointlari."""

from django.urls import path

from . import api

app_name = "reviews"

urlpatterns = [
    path("api/rate/", api.rate_movie, name="api_rate"),
    path("api/review/", api.submit_review, name="api_review"),
]
