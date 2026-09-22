"""Serial katalogi URL lari. movies/urls.py bilan bir xil naqsh."""

from django.urls import path

from . import views

app_name = "series"

urlpatterns = [
    # Seriallar ro'yxati ham umumiy katalogda (`core:catalog`).
    path("series/", views.SeriesListRedirectView.as_view(), name="series_list"),
    path("series/<slug:slug>/", views.SeriesDetailView.as_view(), name="series_detail"),
]
