"""Serial katalogi — public sahifalar: ro'yxat va detail (epizod pleeri bilan).

Seriallar ro'yxati (filtr bilan) alohida emas -- u umumiy katalogda,
`core/catalog.py` da: bitta filtr kino, multfilm va seriallarga birdek
ishlaydi. Bu yerda faqat detail sahifasi va katalogga yo'naltirish qoladi.

Series/Episode'da litsenziya (LicenseType) yo'q, shuning uchun ko'rish
ruxsati faqat `is_published` + video manbasi borligiga
(`Episode.can_watch`) qaraladi.
"""

from django.db.models import Count, F, Q
from django.views.generic import DetailView

from movies.views import CatalogRedirectView
from reviews.models import Rating, Review

from .models import Episode, Series


class SeriesListRedirectView(CatalogRedirectView):
    """`/series/` -> umumiy katalog, «Seriallar» turi tanlangan holda."""

    content_type = "series"


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
            .select_related("language")
            .prefetch_related("genres", "cast_members__actor", "directors", "countries")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        series = self.object
        user = self.request.user

        # `published_count` — fasl tabidagi epizodlar soni uchun. Shablonda
        # sanab bo'lmaydi (chop etilmaganlari chiqarib tashlanadi), shuning
        # uchun bitta so'rovda annotatsiya qilinadi.
        seasons = (
            series.seasons.filter(is_published=True)
            .annotate(
                published_count=Count("episodes", filter=Q(episodes__is_published=True))
            )
            .prefetch_related("episodes")
            .order_by("number")
        )
        context["seasons"] = seasons

        # Joriy epizod: ?episode=<id> orqali, aks holda birinchi chop
        # etilgan epizod.
        published_episodes = Episode.objects.filter(
            season__series=series, season__is_published=True, is_published=True
        ).select_related("season", "season__series").order_by(
            "season__number", "episode_number"
        )

        current_episode = None
        episode_id = self.request.GET.get("episode")
        if episode_id and episode_id.isdigit():
            current_episode = published_episodes.filter(pk=episode_id).first()
        if current_episode is None:
            current_episode = published_episodes.first()

        context["current_episode"] = current_episode
        # Fasl tablaridan qaysi biri ochiq turishi: joriy epizodniki, aks
        # holda birinchisi.
        context["active_season_id"] = (
            current_episode.season_id if current_episode else (seasons[0].pk if seasons else None)
        )
        # `can_watch` (chop etilgan + video bor) USTIGA obuna tekshiruvi —
        # pleer faqat shu bayroq True bo'lganda ko'rsatiladi (Movie bilan
        # bir xil naqsh).
        context["can_play"] = bool(current_episode and current_episode.is_watchable_by(user))

        if current_episode and context["can_play"] and user.is_authenticated:
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

        # Tasdiqlangan sharhlar — Movie bilan bir xil naqsh.
        context["reviews"] = (
            Review.objects.filter(series=series, status=Review.Status.APPROVED)
            .select_related("user", "user__profile")
            .order_by("-created_at")[:20]
        )

        if user.is_authenticated:
            rating = Rating.objects.filter(user=user, series=series).first()
            context["user_rating"] = rating.score if rating else 0
            context["user_review"] = Review.objects.filter(user=user, series=series).first()
        else:
            context["user_rating"] = 0

        context["star_range"] = [1, 2, 3, 4, 5]

        return context
