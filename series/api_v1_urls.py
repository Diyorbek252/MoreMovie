"""DRF router — `/api/v1/series/...`."""

from rest_framework.routers import DefaultRouter

from .api_v1 import SeriesViewSet

router = DefaultRouter()
router.register("series", SeriesViewSet, basename="api-series")

urlpatterns = router.urls
