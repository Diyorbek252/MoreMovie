"""DRF API — film ro'yxati, detali va foydalanuvchi harakatlari.

Eski `movies/api.py` (JsonResponse) va `movies/views.py` (HTML) dagi
biznes-mantiq shu yerga ko'chiriladi, o'zi o'zgarmaydi. Eski endpointlar
frontend to'liq ko'chirilgunicha ishlab turadi (CLAUDE.md rejasi, 6-bosqich).
"""

from django.conf import settings
from django.db.models import F
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from shop.models import CinepointTransaction
from shop.services import adjust_balance, has_earned

from .filters import MovieFilter
from .models import Favorite, Genre, Movie, ViewHistory, Watchlist
from .serializers import GenreSerializer, MovieCardSerializer, MovieDetailSerializer


class GenreViewSet(viewsets.ReadOnlyModelViewSet):
    """`GET /api/v1/genres/` — navbar/footer janr ro'yxati uchun."""

    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    pagination_class = None
    permission_classes = [permissions.AllowAny]


class MovieViewSet(viewsets.ReadOnlyModelViewSet):
    """`GET /api/v1/movies/` va `GET /api/v1/movies/<slug>/`.

    Yozish harakatlari (watchlist, favorite, progress, view) shu
    ViewSet'ning `@action`lari — ular film obyektiga bog'liq bo'lgani
    uchun (`get_object()` orqali 404/litsenziya tekshiruvi bepul keladi).
    """

    lookup_field = "slug"
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = MovieFilter
    search_fields = ["title", "original_title", "description", "genres__name", "directors__full_name"]
    ordering_fields = ["created_at", "views_count", "avg_rating", "release_year", "title"]
    ordering = ["-created_at"]

    def get_queryset(self):
        base = Movie.objects.published()
        if self.action == "retrieve":
            return base.select_related("language").prefetch_related(
                "genres", "screenshots", "cast_members__actor", "videos", "directors", "countries"
            )
        return base.with_relations()

    def get_serializer_class(self):
        return MovieDetailSerializer if self.action == "retrieve" else MovieCardSerializer

    def get_permissions(self):
        if self.action in {"toggle_watchlist", "toggle_favorite", "progress", "register_view"}:
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    def retrieve(self, request, *args, **kwargs):
        """Detail o'qishning o'zi ko'rishlar sonini oshirmaydi (eski
        `MovieDetailView` dagi GET'da F() oshirish xatti-harakati bu yerda
        ATAYLAB ko'chirilmagan — SSR prefetch sonni shishiradi). Buning
        o'rniga pleer haqiqatan ishga tushganda frontend `register_view`
        action'ini alohida chaqiradi."""
        return super().retrieve(request, *args, **kwargs)

    # ------------------------------------------------------------ harakatlar

    @action(detail=True, methods=["post"], url_path="watchlist")
    def toggle_watchlist(self, request, slug=None):
        return self._toggle(request, Watchlist)

    @action(detail=True, methods=["post"], url_path="favorite")
    def toggle_favorite(self, request, slug=None):
        return self._toggle(request, Favorite)

    def _toggle(self, request, model):
        movie = self.get_object()
        entry, created = model.objects.get_or_create(user=request.user, movie=movie)
        if not created:
            entry.delete()
        return Response(
            {
                "added": created,
                "count": model.objects.filter(user=request.user).count(),
                "message": "Ro'yxatga qo'shildi" if created else "Ro'yxatdan olib tashlandi",
            }
        )

    @action(detail=True, methods=["post"], url_path="progress")
    def progress(self, request, slug=None):
        """Player har 15 soniyada to'xtagan joyni yuboradi.

        Body: {"seconds": <int>, "finished": <bool>}
        """
        movie = self.get_object()

        try:
            seconds = max(0, int(request.data.get("seconds", 0)))
        except (TypeError, ValueError):
            seconds = 0
        finished = bool(request.data.get("finished", False))

        history, _ = ViewHistory.objects.get_or_create(user=request.user, movie=movie)
        # Faqat hozir birinchi marta "tugatilgan" holatga o'tsa mukofot
        # beramiz — aks holda filmni qayta-qayta ko'rib cinepoint yig'ib
        # bo'lmaydi (movies/api.py:save_progress bilan bir xil mantiq).
        newly_finished = finished and not history.is_finished

        history.progress_seconds = seconds
        history.is_finished = finished
        history.save(update_fields=["progress_seconds", "is_finished"])

        if newly_finished and not has_earned(request.user, CinepointTransaction.Reason.MOVIE_WATCH, movie):
            adjust_balance(
                request.user,
                settings.CINEPOINT_MOVIE_REWARD,
                CinepointTransaction.Reason.MOVIE_WATCH,
                note=f"«{movie.title}» filmini ko'rish uchun",
                related=movie,
            )

        return Response({"saved": True, "seconds": seconds})

    @action(detail=True, methods=["post"], url_path="view")
    def register_view(self, request, slug=None):
        """Pleer haqiqatan ishga tushganda chaqiriladi — eski
        `MovieDetailView` dagi GET'da F() oshirish o'rnini bosadi (bu
        yerda SSR prefetch son shishirmaydi, faqat haqiqiy tomosha
        hisoblanadi). Faqat `can_play=True` bo'lganda oshiriladi."""
        movie = self.get_object()
        if movie.is_watchable_by(request.user):
            Movie.objects.filter(pk=movie.pk).update(views_count=F("views_count") + 1)
        return Response({"ok": True})
