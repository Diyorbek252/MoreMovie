"""Serial katalogi URL lari. movies/urls.py bilan bir xil naqsh."""

from django.urls import path

from . import views

app_name = "series"

urlpatterns = [
    path("series/", views.SeriesListView.as_view(), name="series_list"),
    path("series/<slug:slug>/", views.SeriesDetailView.as_view(), name="series_detail"),
]
