"""Serial / fasl / epizod modellari.

MUHIM: bu modellar FAQAT boshqaruv panelida boshqariladi. Public sahifasi
yo'q — shu sababdan `Series` da `get_absolute_url()` ATAYLAB yo'q va bu
ilova `config/urls.py` ga hech qachon ulanmaydi (`series/urls.py` ham
yo'q). Kelajakda public sahifa kerak bo'lsa, shu ikkalasini qo'shish
kifoya — boshqa hech narsa o'zgarmaydi.
"""

from django.db import models

from movies.models import (
    AgeRating,
    Category,
    Country,
    Genre,
    Language,
    Movie,
    Person,
    TimeStampedModel,
    unique_slugify,
)


class SeriesQuerySet(models.QuerySet):
    """Movie.MovieQuerySet bilan bir xil naqsh — dashboard ro'yxatlarida ishlatiladi."""

    def published(self):
        return self.filter(is_published=True)

    def with_relations(self):
        return self.select_related("country", "language", "director").prefetch_related(
            "genres"
        )


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
    country = models.ForeignKey(
        Country, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="series", verbose_name="davlat",
    )
    language = models.ForeignKey(
        Language, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="series", verbose_name="til",
    )
    director = models.ForeignKey(
        Person, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="directed_series", verbose_name="rejissyor",
    )
    genres = models.ManyToManyField(Genre, related_name="series", blank=True, verbose_name="janrlar")
    categories = models.ManyToManyField(
        Category, related_name="series", blank=True, verbose_name="kategoriyalar",
    )
    cast = models.ManyToManyField(
        Person, through="SeriesCast", related_name="acted_series",
        blank=True, verbose_name="aktyorlar",
    )

    # --- Holat ---
    is_featured = models.BooleanField("tanlangan", default=False)
    is_trending = models.BooleanField("trendda", default=False)
    is_published = models.BooleanField("chop etilgan", default=False)
    views_count = models.PositiveIntegerField("ko'rishlar soni", default=0, editable=False)

    objects = SeriesQuerySet.as_manager()

    class Meta:
        verbose_name = "serial"
        verbose_name_plural = "seriallar"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_published", "-created_at"]),
            models.Index(fields=["is_published", "is_featured"]),
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


class SeriesCast(models.Model):
    """Movie.MovieCast bilan bir xil naqsh — serial aktyorlar tarkibi."""

    series = models.ForeignKey(
        Series, on_delete=models.CASCADE, related_name="cast_members", verbose_name="serial"
    )
    person = models.ForeignKey(
        Person, on_delete=models.CASCADE, related_name="series_roles", verbose_name="aktyor"
    )
    character_name = models.CharField("rol nomi", max_length=150, blank=True)
    order = models.PositiveSmallIntegerField("tartib", default=0)

    class Meta:
        verbose_name = "serial aktyor roli"
        verbose_name_plural = "serial aktyorlar tarkibi"
        ordering = ["order", "id"]
        constraints = [
            models.UniqueConstraint(fields=["series", "person"], name="unique_series_person_role")
        ]

    def __str__(self):
        if self.character_name:
            return f"{self.person} — {self.character_name}"
        return str(self.person)


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
