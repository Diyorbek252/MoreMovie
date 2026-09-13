"""Serial katalogi — public sahifalar: ro'yxat va detail (epizod pleeri bilan).

movies/views.py dagi naqshlarni takrorlaydi (QueryStringMixin, SORT_OPTIONS
lug'ati). Farqi: Series/Episode'da litsenziya (LicenseType) yo'q, shuning
uchun ko'rish ruxsati faqat `is_published` + video manbasi borligiga
(`Episode.can_watch`) qaraladi.
"""

from django.conf import settings
from django.db.models import Count, F, Q
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView

from movies.models import Genre
from movies.views import QueryStringMixin

from .models import Episode, Series


class SeriesListView(QueryStringMixin, ListView):
    """Barcha seriallar — qidiruv, janr filtri va saralash bilan."""

    model = Series
    template_name = "series/series_list.html"
    context_object_name = "series_list"
    paginate_by = settings.MOVIES_PER_PAGE

    SORT_OPTIONS = {
        "latest": ("-created_at", "Eng yangi"),
        "popular": ("-views_count", "Eng mashhur"),
        "rating": ("-imdb_rating", "Yuqori reyting"),
        "year": ("-release_year", "Yil bo'yicha"),
        "az": ("title", "A-Z"),
    }

    def get_queryset(self):
        queryset = Series.objects.published().with_relations()
        params = self.request.GET

        if query := params.get("q", "").strip():
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(original_title__icontains=query)
                | Q(description__icontains=query)
                | Q(genres__name__icontains=query)
            ).distinct()

        if genre := params.get("genre"):
            queryset = queryset.filter(genres__slug=genre)

        sort = params.get("sort", "latest")
        order_field = self.SORT_OPTIONS.get(sort, self.SORT_OPTIONS["latest"])[0]
        return queryset.order_by(order_field)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        params = self.request.GET

        context.update(
            {
                "genres": Genre.objects.all(),
                "sort_options": self.SORT_OPTIONS,
                "current": {
                    "q": params.get("q", ""),
                    "genre": params.get("genre", ""),
                    "sort": params.get("sort", "latest"),
                },
                "has_filters": any(params.get(key) for key in ("q", "genre")),
            }
        )
        return context


class SeriesDetailView(DetailView):
    """Serial sahifasi — ma'lumot, fasl/epizod ro'yxati, joriy epizod pleeri.

    Alohida `/watch/` yo'li yo'q — Movie bilan bir xil naqsh: pleer shu
    sahifaning o'zida (`#player`), tanlangan epizod `?episode=<id>` query
    parametri orqali aniqlanadi.
    """

    model = Series
    template_name = "series/series_detail.html"
    context_object_name = "series"

    def get_queryset(self):
        return (
            Series.objects.published()
            .select_related("country", "language")
            .prefetch_related("genres", "cast_members__actor", "directors")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        series = self.object
        user = self.request.user

        seasons = (
            series.seasons.filter(is_published=True)
            .prefetch_related("episodes")
            .order_by("number")
        )
        context["seasons"] = seasons

        # Joriy epizod: ?episode=<id> orqali, aks holda birinchi chop
        # etilgan epizod.
        published_episodes = Episode.objects.filter(
            season__series=series, season__is_published=True, is_published=True
        ).select_related("season").order_by("season__number", "episode_number")

        current_episode = None
        episode_id = self.request.GET.get("episode")
        if episode_id and episode_id.isdigit():
            current_episode = published_episodes.filter(pk=episode_id).first()
        if current_episode is None:
            current_episode = published_episodes.first()

        context["current_episode"] = current_episode

        if current_episode and current_episode.can_watch and user.is_authenticated:
            # Ko'rishlar hisoblagichi — F() bilan atomik oshiriladi. Movie'dan
            # farqli — bu yerda resume/ViewHistory kuzatilmaydi (ViewHistory
            # faqat Movie'ga bog'langan), shuning uchun pleer har doim
            # boshidan boshlanadi.
            Episode.objects.filter(pk=current_episode.pk).update(
                views_count=F("views_count") + 1
            )

        # O'xshash seriallar — bir xil janrdagilar.
        genre_ids = list(series.genres.values_list("id", flat=True))
        context["similar_series"] = (
            Series.objects.published()
            .with_relations()
            .filter(genres__id__in=genre_ids)
            .exclude(pk=series.pk)
            .annotate(shared=Count("genres"))
            .order_by("-shared")
            .distinct()[:12]
        )

        return context
