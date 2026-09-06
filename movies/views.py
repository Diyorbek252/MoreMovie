"""Film katalogi view'lari: ro'yxat, filtr, detail, watch, janr, qidiruv."""

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, F, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView, TemplateView

from reviews.models import Rating, Review

from .models import Genre, Movie, ViewHistory


class QueryStringMixin:
    """Sahifalash havolalarida joriy filtrlarni saqlab qolish uchun."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop("page", None)
        context["querystring"] = params.urlencode()
        return context


class MovieListView(QueryStringMixin, ListView):
    """Barcha filmlar — qidiruv, filtr, saralash va sahifalash bilan."""

    model = Movie
    template_name = "movies/movie_list.html"
    context_object_name = "movies"
    paginate_by = settings.MOVIES_PER_PAGE

    # Foydalanuvchi yuborgan `sort` qiymati shu lug'at orqali tekshiriladi —
    # bevosita order_by() ga uzatilmaydi (SQL injection va xatoning oldini oladi).
    SORT_OPTIONS = {
        "latest": ("-created_at", "Eng yangi"),
        "popular": ("-views_count", "Eng mashhur"),
        "rating": ("-avg_rating", "Yuqori reyting"),
        "year": ("-release_year", "Yil bo'yicha"),
        "az": ("title", "A-Z"),
    }

    def get_queryset(self):
        queryset = Movie.objects.published().with_relations()
        params = self.request.GET

        # --- Qidiruv ---
        query = params.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(original_title__icontains=query)
                | Q(description__icontains=query)
                | Q(genres__name__icontains=query)
                | Q(director__full_name__icontains=query)
                | Q(cast__full_name__icontains=query)
            ).distinct()

        # --- Filtrlar ---
        if genre := params.get("genre"):
            queryset = queryset.filter(genres__slug=genre)

        if year := params.get("year"):
            if year.isdigit():
                queryset = queryset.filter(release_year=int(year))

        if language := params.get("language"):
            queryset = queryset.filter(language__slug=language)

        if country := params.get("country"):
            queryset = queryset.filter(country__slug=country)

        if rating := params.get("rating"):
            # "7" -> reytingi 7.0 va undan yuqori (10 ballik shkalada).
            try:
                queryset = queryset.filter(imdb_rating__gte=float(rating))
            except ValueError:
                pass

        # --- Saralash ---
        sort = params.get("sort", "latest")
        order_field = self.SORT_OPTIONS.get(sort, self.SORT_OPTIONS["latest"])[0]
        return queryset.order_by(order_field)

    def get_context_data(self, **kwargs):
        from .models import Country, Language

        context = super().get_context_data(**kwargs)
        params = self.request.GET

        context.update(
            {
                "genres": Genre.objects.all(),
                "countries": Country.objects.all(),
                "languages": Language.objects.all(),
                # Filtr uchun mavjud yillar — faqat bazada bori.
                "years": (
                    Movie.objects.published()
                    .values_list("release_year", flat=True)
                    .distinct()
                    .order_by("-release_year")
                ),
                "sort_options": self.SORT_OPTIONS,
                # Formadagi tanlangan qiymatlarni qayta ko'rsatish uchun.
                "current": {
                    "q": params.get("q", ""),
                    "genre": params.get("genre", ""),
                    "year": params.get("year", ""),
                    "language": params.get("language", ""),
                    "country": params.get("country", ""),
                    "rating": params.get("rating", ""),
                    "sort": params.get("sort", "latest"),
                },
                "has_filters": any(
                    params.get(key)
                    for key in ("q", "genre", "year", "language", "country", "rating")
                ),
            }
        )
        return context


class MovieDetailView(DetailView):
    """Film sahifasi — ma'lumot, treyler, kadrlar, sharhlar, o'xshash filmlar."""

    model = Movie
    template_name = "movies/movie_detail.html"
    context_object_name = "movie"

    def get_queryset(self):
        return (
            Movie.objects.published()
            .select_related("country", "language", "director")
            .prefetch_related("genres", "screenshots", "cast_members__person")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        movie = self.object

        # Tasdiqlangan sharhlar.
        context["reviews"] = (
            Review.objects.filter(movie=movie, status=Review.Status.APPROVED)
            .select_related("user", "user__profile")
            .order_by("-created_at")[:20]
        )

        # O'xshash filmlar — bir xil janrdagilar, mos janrlar soni bo'yicha.
        genre_ids = list(movie.genres.values_list("id", flat=True))
        context["similar_movies"] = (
            Movie.objects.published()
            .with_relations()
            .filter(genres__id__in=genre_ids)
            .exclude(pk=movie.pk)
            .annotate(shared=Count("genres"))
            .order_by("-shared", "-avg_rating")
            .distinct()[:12]
        )

        # Joriy foydalanuvchining bahosi va sharhi.
        user = self.request.user
        if user.is_authenticated:
            rating = Rating.objects.filter(user=user, movie=movie).first()
            context["user_rating"] = rating.score if rating else 0
            context["user_review"] = Review.objects.filter(user=user, movie=movie).first()
        else:
            context["user_rating"] = 0

        # Yulduzlarni chizish uchun 1..5 ro'yxati.
        context["star_range"] = [1, 2, 3, 4, 5]

        return context


class WatchView(LoginRequiredMixin, DetailView):
    """Video player sahifasi.

    Kirish uchun tizimga kirgan bo'lish shart. Bundan tashqari film
    `can_watch` shartini qanoatlantirishi kerak — bu litsenziya tekshiruvi.
    """

    model = Movie
    template_name = "movies/watch.html"
    context_object_name = "movie"

    def get_queryset(self):
        return (
            Movie.objects.published()
            .select_related("country", "language", "director")
            .prefetch_related("genres")
        )

    def get_object(self, queryset=None):
        movie = super().get_object(queryset)

        # Huquqiy tekshiruv — litsenziya ruxsat bermasa 403.
        if not movie.can_watch:
            raise PermissionDenied(
                "Bu film uchun to'liq versiyani ko'rish imkoni yo'q. "
                "Faqat rasmiy treyler mavjud."
            )

        return movie

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        movie = self.object

        # Ko'rishlar hisoblagichi — F() bilan atomik oshiriladi (race condition yo'q).
        Movie.objects.filter(pk=movie.pk).update(views_count=F("views_count") + 1)

        # Oldingi to'xtagan joyni topamiz.
        history = ViewHistory.objects.filter(user=self.request.user, movie=movie).first()
        context["resume_at"] = history.progress_seconds if history else 0

        genre_ids = list(movie.genres.values_list("id", flat=True))
        context["similar_movies"] = (
            Movie.objects.published()
            .with_relations()
            .filter(genres__id__in=genre_ids)
            .exclude(pk=movie.pk)
            .distinct()[:12]
        )

        return context


class GenreListView(TemplateView):
    """Barcha janrlar sahifasi."""

    template_name = "movies/genre_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["genres"] = (
            Genre.objects.annotate(
                movie_total=Count("movies", filter=Q(movies__is_published=True))
            )
            .filter(movie_total__gt=0)
            .order_by("-movie_total")
        )
        return context


class GenreDetailView(QueryStringMixin, ListView):
    """Bitta janrdagi filmlar."""

    template_name = "movies/genre_detail.html"
    context_object_name = "movies"
    paginate_by = settings.MOVIES_PER_PAGE

    def get_queryset(self):
        self.genre = get_object_or_404(Genre, slug=self.kwargs["slug"])
        return (
            Movie.objects.published()
            .with_relations()
            .filter(genres=self.genre)
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["genre"] = self.genre
        return context


class SearchView(QueryStringMixin, ListView):
    """Qidiruv natijalari sahifasi (to'liq sahifa varianti)."""

    template_name = "movies/search_results.html"
    context_object_name = "movies"
    paginate_by = settings.MOVIES_PER_PAGE

    def get_queryset(self):
        self.query = self.request.GET.get("q", "").strip()
        if not self.query:
            return Movie.objects.none()

        return (
            Movie.objects.published()
            .with_relations()
            .filter(
                Q(title__icontains=self.query)
                | Q(original_title__icontains=self.query)
                | Q(description__icontains=self.query)
                | Q(genres__name__icontains=self.query)
                | Q(director__full_name__icontains=self.query)
                | Q(cast__full_name__icontains=self.query)
            )
            .distinct()
            .order_by("-views_count")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.query
        return context


def search_suggest(request):
    """Navbar jonli qidiruvi uchun JSON endpoint.

    GET /api/search/?q=...  ->  {"results": [...], "total": n}
    Autentifikatsiya talab qilinmaydi — faqat chop etilgan filmlar qaytariladi.
    """
    query = request.GET.get("q", "").strip()

    if len(query) < 2:
        return JsonResponse({"results": [], "total": 0})

    movies = (
        Movie.objects.published()
        .select_related("director")
        .filter(
            Q(title__icontains=query)
            | Q(original_title__icontains=query)
            | Q(genres__name__icontains=query)
            | Q(director__full_name__icontains=query)
            | Q(cast__full_name__icontains=query)
        )
        .distinct()
        .order_by("-views_count")[:8]
    )

    results = [
        {
            "title": movie.title,
            "year": movie.release_year,
            "quality": movie.get_quality_display(),
            "rating": movie.display_rating,
            "url": movie.get_absolute_url(),
            "poster": movie.poster.url if movie.poster else "",
        }
        for movie in movies
    ]

    return JsonResponse({"results": results, "total": len(results)})
