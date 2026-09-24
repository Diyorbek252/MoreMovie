"""DRF router — `/api/v1/movies/...`."""

from rest_framework.routers import DefaultRouter

from .api_v1 import GenreViewSet, MovieViewSet

router = DefaultRouter()
router.register("movies", MovieViewSet, basename="api-movie")
router.register("genres", GenreViewSet, basename="api-genre")

urlpatterns = router.urls
