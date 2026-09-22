"""Film katalogi view'lari: ro'yxat, filtr, detail (pleer bilan), janr, qidiruv."""

from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Count, F, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import DetailView, ListView, RedirectView, TemplateView

from reviews.models import Rating, Review
from series.models import Series

from .models import Actor, Category, Director, Genre, Movie, ViewHistory


class QueryStringMixin:
    """Sahifalash havolalarida joriy filtrlarni saqlab qolish uchun."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop("page", None)
        context["querystring"] = params.urlencode()
        return context


class CatalogRedirectView(RedirectView):
    """Eski ro'yxat sahifalarini umumiy katalogga olib o'tadi.

    Filtr endi bitta -- `core.catalog.CatalogView` (`/katalog/`) kino,
    multfilm va seriallarni birga filtrlaydi. Parametr nomlari (q, genre,
    year, language, country, rating, sort) eski sahifalar bilan aynan bir
    xil, shuning uchun mavjud havolalar va bookmarklar ishlayveradi --
    faqat `type` qo'shiladi.
    """

    permanent = False

    #: Katalogda oldindan tanlanadigan kontent turi.
    content_type = "movie"

    def get_redirect_url(self, *args, **kwargs):
        params = self.request.GET.copy()
        params["type"] = self.content_type
        return f"{reverse('core:catalog')}?{params.urlencode()}"


class MovieListRedirectView(CatalogRedirectView):
    content_type = "movie"


class MovieDetailView(DetailView):
    """Film sahifasi — ma'lumot, pleer, kadrlar, sharhlar, o'xshash filmlar.

    Pleer avval alohida `/watch/<slug>/` sahifasida edi — endi shu
    sahifaning o'zida (`#player` bo'limida) ko'rsatiladi. Video manbasi
    faqat autentifikatsiya qilingan va `can_watch` bo'lgan holatda
    shablonga uzatiladi (qarang: movie_detail.html), shu bilan avvalgi
    `LoginRequiredMixin` orqali ta'minlangan cheklov saqlanib qoladi —
    farqi shundaki, endi butun sahifa emas, faqat pleerning o'zi
    tizimga kirishni talab qiladi.
    """

    model = Movie
    template_name = "movies/movie_detail.html"
    context_object_name = "movie"

    def get_queryset(self):
        return (
            Movie.objects.published()
            .select_related("language")
            .prefetch_related(
                "genres", "screenshots", "cast_members__actor", "videos", "directors", "countries"
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        movie = self.object
        user = self.request.user

        # Pleerdagi sifat ro'yxati — shablonda bir necha marta kerak
        # bo'lgani uchun bir marta hisoblab, kontekstga qo'yamiz.
        context["video_sources"] = movie.video_sources

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

        context["resume_at"] = 0
        # `can_watch` (litsenziya) USTIGA premium-obuna tekshiruvi —
        # pleer faqat shu bayroq True bo'lganda ko'rsatiladi.
        context["can_play"] = movie.is_watchable_by(user)

        if user.is_authenticated:
            rating = Rating.objects.filter(user=user, movie=movie).first()
            context["user_rating"] = rating.score if rating else 0
            context["user_review"] = Review.objects.filter(user=user, movie=movie).first()

            if context["can_play"]:
                # Ko'rishlar hisoblagichi — F() bilan atomik oshiriladi
                # (race condition yo'q). Faqat haqiqatan pleer
                # ko'rsatiladigan holatda oshiriladi.
                Movie.objects.filter(pk=movie.pk).update(views_count=F("views_count") + 1)

                # Oldingi to'xtagan joyni topamiz.
                history = ViewHistory.objects.filter(user=user, movie=movie).first()
                context["resume_at"] = history.progress_seconds if history else 0
        else:
            context["user_rating"] = 0

        # Yulduzlarni chizish uchun 1..5 ro'yxati.
        context["star_range"] = [1, 2, 3, 4, 5]

        return context


class WatchRedirectView(RedirectView):
    """Eski `/watch/<slug>/` havolalarini yangi joyga yo'naltiradi.

    Pleer endi mustaqil sahifa emas — film detali bilan bitta sahifada
    (`#player` bo'limi). Signat/bookmark qilingan eski havolalar
    buzilmasligi uchun doimiy (301) yo'naltirish saqlanadi.
    """

    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        return reverse("movies:movie_detail", kwargs={"slug": kwargs["slug"]}) + "#player"


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
        context["genre_rail"] = self._genre_rail()
        return context

    def _genre_rail(self):
        """Bosh sahifadagi bilan bir xil dizayndagi tezkor janr almashtirish
        qatori — bu sahifa faqat filmlarni ko'rsatgani uchun (multfilm/serial
        emas) sanoq ham FAQAT filmlar bo'yicha hisoblanadi.
        """
        genres = (
            Genre.objects.annotate(
                movie_total=Count("movies", filter=Q(movies__is_published=True))
            )
            .filter(movie_total__gt=0)
            .order_by("-movie_total", "name")
        )
        return [
            {
                "genre": genre,
                "url": genre.get_absolute_url(),
                "active": genre.pk == self.genre.pk,
            }
            for genre in genres
        ]


class CategoryDetailView(QueryStringMixin, ListView):
    """Bitta kategoriyadagi filmlar — GenreDetailView bilan bir xil naqsh."""

    template_name = "movies/category_detail.html"
    context_object_name = "movies"
    paginate_by = settings.MOVIES_PER_PAGE

    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs["slug"], is_active=True)
        return (
            Movie.objects.published()
            .with_relations()
            .filter(categories=self.category)
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category"] = self.category
        return context


def _paginate_movie_series(request, movie_qs, series_qs, per_page):
    """Kino/multfilm va serial querysetlarini BIRGA (yil bo'yicha) sahifalaydi.

    `core.catalog.CatalogView` dagi bilan bir xil naqsh: to'liq obyektlar
    emas, avval faqat `(tur, pk, saralash_kaliti)` juftliklari olinadi —
    shu bilan sahifalash yengil bo'ladi, so'ng FAQAT joriy sahifadagi
    yozuvlar to'liq obyekt sifatida (`with_relations()` bilan) yuklanadi.

    Rejissyor/aktyor sahifalari FAQAT filmlarni ko'rsatib kelgan edi —
    aktyor yoki rejissyor serialda ham qatnashgan bo'lishi mumkin, shu
    sabab ikkalasi ham birga chiqishi kerak (xuddi umumiy katalogdagidek).
    """
    rows = [("movie", pk, year) for pk, year in movie_qs.values_list("pk", "release_year")]
    rows += [("series", pk, year) for pk, year in series_qs.values_list("pk", "release_year")]

    # `None` yil (masalan kiritilmagan) tartiblashni buzmasligi uchun oxiriga tushadi.
    rows.sort(key=lambda row: (row[2] is None, row[2] or 0), reverse=True)

    paginator = Paginator(rows, per_page)
    page_obj = paginator.get_page(request.GET.get("page"))

    movie_ids = [pk for kind, pk, _ in page_obj.object_list if kind == "movie"]
    series_ids = [pk for kind, pk, _ in page_obj.object_list if kind == "series"]

    movies = {obj.pk: obj for obj in Movie.objects.with_relations().filter(pk__in=movie_ids)}
    series = {obj.pk: obj for obj in Series.objects.with_relations().filter(pk__in=series_ids)}

    items = []
    for kind, pk, _ in page_obj.object_list:
        obj = movies.get(pk) if kind == "movie" else series.get(pk)
        if obj is not None:
            items.append({"kind": kind, "object": obj})

    return {
        "items": items,
        "page_obj": page_obj,
        "paginator": paginator,
        "is_paginated": page_obj.has_other_pages(),
    }


class DirectorDetailView(QueryStringMixin, TemplateView):
    """Bitta rejissyor suratga olgan kino, multfilm VA seriallar.

    Ilgari faqat `Movie` filtrlangan edi — rejissyor serial suratga
    olgan bo'lsa ham "hech narsa yo'q" chiqib qolardi. Endi umumiy
    katalog bilan bir xil naqshda ikkalasi ham birga ko'rsatiladi.
    """

    template_name = "movies/director_detail.html"

    def get(self, request, *args, **kwargs):
        self.director = get_object_or_404(Director, slug=kwargs["slug"])
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        movie_qs = Movie.objects.published().filter(directors=self.director)
        series_qs = Series.objects.published().filter(directors=self.director)
        context["director"] = self.director
        context.update(_paginate_movie_series(self.request, movie_qs, series_qs, settings.MOVIES_PER_PAGE))
        return context


class ActorDetailView(QueryStringMixin, TemplateView):
    """Bitta aktyor qatnashgan kino, multfilm VA seriallar.

    Ilgari faqat `Movie` filtrlangan edi — aktyor faqat serialda
    o'ynagan bo'lsa "hech narsa yo'q" chiqib qolardi. Endi umumiy
    katalog bilan bir xil naqshda ikkalasi ham birga ko'rsatiladi.
    """

    template_name = "movies/actor_detail.html"

    def get(self, request, *args, **kwargs):
        self.actor = get_object_or_404(Actor, slug=kwargs["slug"])
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        movie_qs = Movie.objects.published().filter(cast=self.actor)
        series_qs = Series.objects.published().filter(cast=self.actor)
        context["actor"] = self.actor
        context.update(_paginate_movie_series(self.request, movie_qs, series_qs, settings.MOVIES_PER_PAGE))
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
                | Q(directors__full_name__icontains=self.query)
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
        .filter(
            Q(title__icontains=query)
            | Q(original_title__icontains=query)
            | Q(genres__name__icontains=query)
            | Q(directors__full_name__icontains=query)
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
            "imdb": float(movie.imdb_rating),
            "url": movie.get_absolute_url(),
            "poster": movie.poster.url if movie.poster else "",
        }
        for movie in movies
    ]

    return JsonResponse({"results": results, "total": len(results)})
