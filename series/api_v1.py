"""DRF API — serial ro'yxati/detali va epizod ko'rish hisoblagichi.

Seriallar ro'yxati eski saytda umumiy `core:catalog` ga tegishli edi —
API'da ham xuddi shunday: bu ViewSet faqat detail va epizod harakatlari
uchun, birlashtirilgan ro'yxat `core/api_v1.py::CatalogAPIView` da
(Movie + Series birga).
"""

from django.db.models import F
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Episode, Series
from .serializers import SeriesCardSerializer, SeriesDetailSerializer


class SeriesViewSet(viewsets.ReadOnlyModelViewSet):
    """`GET /api/v1/series/` va `GET /api/v1/series/<slug>/`."""

    lookup_field = "slug"
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status"]
    search_fields = ["title", "original_title", "description", "genres__name"]
    ordering_fields = ["created_at", "views_count", "avg_rating", "release_year", "title"]
    ordering = ["-created_at"]

    def get_queryset(self):
        base = Series.objects.published()
        if self.action == "retrieve":
            return base.select_related("language").prefetch_related(
                "genres", "cast_members__actor", "directors", "countries",
                "seasons__episodes",
            )
        return base.with_relations()

    def get_serializer_class(self):
        return SeriesDetailSerializer if self.action == "retrieve" else SeriesCardSerializer

    @action(detail=True, methods=["post"], url_path=r"episodes/(?P<episode_pk>\d+)/view")
    def register_episode_view(self, request, slug=None, episode_pk=None):
        """`POST /api/v1/series/<slug>/episodes/<id>/view/`.

        `SeriesDetailView.get_context_data` dagi GET'da F() oshirish
        o'rnini bosadi — `movies` bilan bir xil naqsh (tuzoq #5), faqat
        haqiqatan tomosha qilinganda hisoblanadi.
        """
        series = self.get_object()
        episode = Episode.objects.filter(pk=episode_pk, season__series=series).first()
        if episode is None:
            return Response({"detail": "Epizod topilmadi."}, status=404)
        if episode.is_watchable_by(request.user):
            Episode.objects.filter(pk=episode.pk).update(views_count=F("views_count") + 1)
        return Response({"ok": True})
