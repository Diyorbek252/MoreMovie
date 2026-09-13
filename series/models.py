"""Serial / fasl / epizod modellari.

Boshqaruv panelidan tashqari endi public sahifasi ham bor (`series/urls.py`,
`series/views.py`) — Movie bilan bir xil naqshda: ro'yxat, detail (epizod
pleeri bilan). Litsenziya (`LicenseType`) tushunchasi Series/Episode'da
yo'q — barcha chop etilgan (`is_published`) va video manbasi bor epizodlar
tizimga kirgan foydalanuvchiga ko'rinadi (qarang: `Episode.can_watch`).
"""

from django.db import models
from django.urls import reverse

from movies.models import (
    Actor,
    AgeRating,
    Category,
    Country,
    Director,
    Genre,
    Language,
    Movie,
    TimeStampedModel,
    unique_slugify,
)


class SeriesQuerySet(models.QuerySet):
    """Movie.MovieQuerySet bilan bir xil naqsh — dashboard ro'yxatlarida ishlatiladi."""

    def published(self):
        return self.filter(is_published=True)

    def with_relations(self):
        return self.select_related("language").prefetch_related(
            "genres", "directors", "countries"
        )

    def newest(self):
        return self.published().with_relations().order_by("-created_at")

    def trending(self):
        return self.published().with_relations().order_by("-views_count", "-created_at")

    def top_rated(self):
        return self.published().with_relations().filter(imdb_rating__gt=0).order_by("-imdb_rating")


class Series(TimeStampedModel):
    """Katalogdagi bitta serial (uning fasllari va epizodlari alohida modellarda)."""

    class Status(models.TextChoices):
        ANNOUNCED = "announced", "E'lon qilingan"
        ONGOING = "ongoing", "Davom etmoqda"
        COMPLETED = "completed", "Tugallangan"

    # --- Matn ---
    title = models.CharField("sarlavha", max_length=200)
    original_title = models.CharField("original sarlavha", max_length=200, blank=True)
    slug = models.SlugField("slug", max_length=220, unique=True, blank=True)
    description = models.TextField("tavsif")
    short_description = models.CharField(
        "qisqa tavsif", max_length=300, blank=True,
        help_text="Bo'sh bo'lsa tavsifdan avtomatik olinadi.",
    )

    # --- Media ---
    poster = models.ImageField(
        "poster", upload_to="series/posters/%Y/%m/", blank=True, null=True,
        help_text="Vertikal (2:3), masalan 500x750.",
    )
    backdrop = models.ImageField(
        "backdrop", upload_to="series/backdrops/%Y/%m/", blank=True, null=True,
    )
    trailer_url = models.URLField("treyler havolasi", blank=True)

    # --- Meta ---
    release_year = models.PositiveSmallIntegerField("boshlangan yil")
    end_year = models.PositiveSmallIntegerField(
        "tugagan yil", null=True, blank=True,
        help_text="Serial hali davom etayotgan bo'lsa bo'sh qoldiring.",
    )
    imdb_rating = models.DecimalField(
        "IMDb reytingi", max_digits=3, decimal_places=1, default=0,
    )
    age_rating = models.CharField(
        "yosh chegarasi", max_length=4, choices=AgeRating.choices, blank=True, default="",
    )
    status = models.CharField(
        "holat", max_length=12, choices=Status.choices, default=Status.ONGOING,
    )

    # --- Aloqalar ---
    countries = models.ManyToManyField(
        Country, related_name="series", blank=True, verbose_name="davlatlar",
        help_text="Bir nechta davlat tanlash mumkin.",
    )
    language = models.ForeignKey(
        Language, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="series", verbose_name="til",
    )
    directors = models.ManyToManyField(
        Director, related_name="directed_series", blank=True, verbose_name="rejissyorlar",
        help_text="Bir nechta rejissyor tanlash mumkin.",
    )
    genres = models.ManyToManyField(Genre, related_name="series", blank=True, verbose_name="janrlar")
    categories = models.ManyToManyField(
        Category, related_name="series", blank=True, verbose_name="kategoriyalar",
    )
    cast = models.ManyToManyField(
        Actor, through="SeriesCast", related_name="acted_series",
        blank=True, verbose_name="aktyorlar",
    )

    # --- Holat ---
    is_featured = models.BooleanField("tanlangan", default=False)
    is_trending = models.BooleanField("trendda", default=False)
    is_premium = models.BooleanField(
        "premium", default=False,
        help_text="Faqat faol Premium obunasi bor foydalanuvchilar tomosha qila oladi.",
    )
    is_published = models.BooleanField("chop etilgan", default=False)
    views_count = models.PositiveIntegerField("ko'rishlar soni", default=0, editable=False)

    # --- Denormalizatsiya (Movie bilan bir xil naqsh) ---
    # Har detail sahifada AVG() hisoblamaslik uchun Rating saqlanganda yangilanadi.
    avg_rating = models.DecimalField(
        "o'rtacha reyting", max_digits=3, decimal_places=2, default=0, editable=False
    )
    rating_count = models.PositiveIntegerField("baholar soni", default=0, editable=False)

    objects = SeriesQuerySet.as_manager()

    class Meta:
        verbose_name = "serial"
        verbose_name_plural = "seriallar"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_published", "-created_at"]),
            models.Index(fields=["is_published", "is_featured"]),
            models.Index(fields=["is_published", "is_premium"]),
            models.Index(fields=["title"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.release_year})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, f"{self.title}-{self.release_year}")
        if not self.short_description:
            self.short_description = self.description[:297].rsplit(" ", 1)[0] + "..."
        super().save(*args, **kwargs)

    @property
    def season_count(self):
        return self.seasons.count()

    @property
    def episode_count(self):
        return Episode.objects.filter(season__series=self).count()

    @property
    def user_rating_display(self):
        """Sayt foydalanuvchilarining o'rtacha bahosi — o'z shkalasida (1-5).

        IMDb reytingi (`imdb_rating`, 0-10) bilan ATAYLAB aralashtirilmaydi —
        Movie.user_rating_display bilan bir xil naqsh.
        """
        if not self.rating_count:
            return None
        return round(float(self.avg_rating), 1)

    def recalculate_rating(self):
        """Reyting o'rtachasini qayta hisoblab, denormalizatsiya
        maydonlarini yangilaydi — Movie.recalculate_rating bilan bir xil
        naqsh, faqat serial uchun."""
        from django.db.models import Avg, Count

        from reviews.models import Review

        approved_user_ids = Review.objects.filter(
            series=self, status=Review.Status.APPROVED
        ).values_list("user_id", flat=True)
        stats = self.ratings.filter(user_id__in=approved_user_ids).aggregate(
            average=Avg("score"), total=Count("id")
        )
        self.avg_rating = round(stats["average"] or 0, 2)
        self.rating_count = stats["total"] or 0
        Series.objects.filter(pk=self.pk).update(
            avg_rating=self.avg_rating, rating_count=self.rating_count
        )

    def get_absolute_url(self):
        return reverse("series:series_detail", kwargs={"slug": self.slug})


class SeriesCast(models.Model):
    """Movie.MovieCast bilan bir xil naqsh — serial aktyorlar tarkibi."""

    series = models.ForeignKey(
        Series, on_delete=models.CASCADE, related_name="cast_members", verbose_name="serial"
    )
    actor = models.ForeignKey(
        Actor, on_delete=models.CASCADE, related_name="series_roles", verbose_name="aktyor"
    )
    character_name = models.CharField("rol nomi", max_length=150, blank=True)
    order = models.PositiveSmallIntegerField("tartib", default=0)

    class Meta:
        verbose_name = "serial aktyor roli"
        verbose_name_plural = "serial aktyorlar tarkibi"
        ordering = ["order", "id"]
        constraints = [
            models.UniqueConstraint(fields=["series", "actor"], name="unique_series_actor_role")
        ]

    def __str__(self):
        if self.character_name:
            return f"{self.actor} — {self.character_name}"
        return str(self.actor)


class Season(TimeStampedModel):
    """Serialning bitta fasli."""

    series = models.ForeignKey(
        Series, on_delete=models.CASCADE, related_name="seasons", verbose_name="serial"
    )
    number = models.PositiveSmallIntegerField("fasl raqami", default=1)
    title = models.CharField("nomi", max_length=200, blank=True)
    description = models.TextField("tavsif", blank=True)
    poster = models.ImageField(
        "poster", upload_to="series/seasons/%Y/%m/", blank=True, null=True,
    )
    year = models.PositiveSmallIntegerField("yil", null=True, blank=True)
    is_published = models.BooleanField("chop etilgan", default=True)

    class Meta:
        verbose_name = "fasl"
        verbose_name_plural = "fasllar"
        ordering = ["series", "number"]
        constraints = [
            models.UniqueConstraint(fields=["series", "number"], name="unique_series_season_number")
        ]

    def __str__(self):
        return f"{self.series.title} — {self.number}-fasl"

    @property
    def display_title(self):
        return self.title or f"{self.number}-fasl"

    @property
    def episode_count(self):
        return self.episodes.count()


class Episode(TimeStampedModel):
    """Faslning bitta epizodi.

    Nomlash Movie modeliga ataylab moslashtirilgan (`is_published`,
    `views_count`, `downloads_count`) — shu bilan dashboard'dagi umumiy
    `.js-toggle` mexanizmi va statistikalar hech qanday maxsus holatsiz
    ishlaydi.
    """

    season = models.ForeignKey(
        Season, on_delete=models.CASCADE, related_name="episodes", verbose_name="fasl"
    )
    episode_number = models.PositiveSmallIntegerField("epizod raqami", default=1)
    title = models.CharField("sarlavha", max_length=200)
    description = models.TextField("tavsif", blank=True)
    thumbnail = models.ImageField(
        "kadr rasmi", upload_to="series/episodes/%Y/%m/", blank=True, null=True,
    )
    video_url = models.URLField("video havolasi", blank=True)
    video_file = models.FileField(
        "video fayl", upload_to="series/videos/%Y/%m/", blank=True, null=True,
    )
    download_url = models.URLField("yuklab olish havolasi", blank=True)
    is_download_allowed = models.BooleanField("yuklab olishga ruxsat", default=False)
    duration_minutes = models.PositiveSmallIntegerField("davomiyligi (daqiqa)", default=0)
    quality = models.CharField(
        "sifat", max_length=4, choices=Movie.Quality.choices, default=Movie.Quality.HD,
    )
    language = models.ForeignKey(
        Language, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="episodes", verbose_name="til",
    )
    air_date = models.DateField("efirga uzatilgan sana", null=True, blank=True)
    views_count = models.PositiveIntegerField("ko'rishlar soni", default=0, editable=False)
    downloads_count = models.PositiveIntegerField(
        "yuklab olishlar soni", default=0, editable=False,
    )
    is_published = models.BooleanField("chop etilgan", default=False)

    class Meta:
        verbose_name = "epizod"
        verbose_name_plural = "epizodlar"
        ordering = ["season", "episode_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["season", "episode_number"], name="unique_season_episode_number"
            )
        ]
        indexes = [models.Index(fields=["is_published", "-created_at"])]

    def __str__(self):
        return f"{self.season} — {self.episode_number}-epizod: {self.title}"

    @property
    def has_video_source(self):
        return bool(self.video_file or self.video_url)

    @property
    def display_thumbnail_url(self):
        """Ko'rsatiladigan rasm — har bir epizod uchun alohida rasm
        so'ralmaydi. O'zining kadr rasmi bo'lmasa, serialning backdrop
        (yoki poster) rasmi ishlatiladi — bir marta yuklangan rasm
        shu serialning barcha epizodlariga qo'llaniladi.
        """
        if self.thumbnail:
            return self.thumbnail.url
        series = self.season.series
        if series.backdrop:
            return series.backdrop.url
        if series.poster:
            return series.poster.url
        return ""

    @property
    def can_watch(self):
        """Movie.can_watch bilan bir xil rol o'ynaydi — litsenziya
        tushunchasi yo'qligi sababli faqat chop etilgan va video manbasi
        bor epizodlar tomosha qilinadi."""
        return self.is_published and self.has_video_source

    def is_watchable_by(self, user):
        """`can_watch` USTIGA obuna tekshiruvi qo'shadi — Movie.is_watchable_by
        bilan bir xil naqsh. "Premium" belgisi butun serialga qo'yiladi
        (`Series.is_premium`) — bitta seriyaning barcha epizodlari birga
        ochiladi yoki birga yopiq turadi.
        """
        if not self.can_watch:
            return False
        if not self.season.series.is_premium:
            return True
        from subscriptions.services import has_premium_access

        return has_premium_access(user)

    @property
    def video_source(self):
        if self.video_file:
            return self.video_file.url
        return self.video_url or ""

    @property
    def duration_display(self):
        if not self.duration_minutes:
            return "—"
        hours, minutes = divmod(self.duration_minutes, 60)
        if hours and minutes:
            return f"{hours}s {minutes}d"
        if hours:
            return f"{hours}s"
        return f"{minutes}d"

    def get_absolute_url(self):
        """Serial detali sahifasidagi shu epizodning pleeriga ishora
        qiladi (`?episode=<id>#player`) — Movie.get_watch_url bilan bir
        xil naqsh, faqat pleer alohida bo'lim emas, query parametr orqali
        tanlanadi."""
        return f"{self.season.series.get_absolute_url()}?episode={self.pk}#player"
