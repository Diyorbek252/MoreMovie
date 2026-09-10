"""Film katalogi modellari.

HUQUQIY ESLATMA
---------------
Bu platforma FAQAT qonuniy tarqatiladigan kontent uchun mo'ljallangan:
public domain, Creative Commons yoki egasi ruxsat bergan (litsenziyalangan)
filmlar. `Movie.license_type` maydoni har bir yozuv uchun shu holatni belgilaydi,
`can_watch` va `can_download` xossalari esa ko'rish/yuklab olish tugmalarini
faqat ruxsat berilgan holatlarda ochadi. Trailer-only yozuvlar uchun saytda
faqat rasmiy treyler ko'rsatiladi.
"""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class TimeStampedModel(models.Model):
    """Yaratilgan/yangilangan vaqtni saqlovchi abstrakt model."""

    created_at = models.DateTimeField("yaratilgan", auto_now_add=True)
    updated_at = models.DateTimeField("yangilangan", auto_now=True)

    class Meta:
        abstract = True


def unique_slugify(instance, value, slug_field="slug"):
    """Model uchun takrorlanmas slug hosil qiladi.

    Bir xil nomli ikkita film qo'shilsa, ikkinchisiga `-2`, `-3` qo'shiladi.
    """
    base = slugify(value, allow_unicode=False) or "element"
    slug = base
    model = instance.__class__
    counter = 2
    queryset = model.objects.all()
    if instance.pk:
        queryset = queryset.exclude(pk=instance.pk)
    while queryset.filter(**{slug_field: slug}).exists():
        slug = f"{base}-{counter}"
        counter += 1
    return slug


class AgeRating(models.TextChoices):
    """Yosh chegarasi belgisi — Movie va (keyinchalik) Series uchun umumiy."""

    ALL = "0+", "0+ (barcha uchun)"
    SIX = "6+", "6+"
    TWELVE = "12+", "12+"
    SIXTEEN = "16+", "16+"
    EIGHTEEN = "18+", "18+ (faqat kattalar)"


# ---------------------------------------------------------------------------
# Ma'lumotnoma modellari (janr, davlat, til, shaxs)
# ---------------------------------------------------------------------------


class Genre(TimeStampedModel):
    """Film janri. Navbar va filtrlar shu modeldan to'ldiriladi."""

    name = models.CharField("nomi", max_length=80, unique=True)
    slug = models.SlugField("slug", max_length=90, unique=True, blank=True)
    description = models.TextField("tavsif", blank=True)
    # Shablonda inline SVG tanlash uchun kalit (masalan "action", "drama").
    icon = models.CharField(
        "ikonka kaliti",
        max_length=40,
        blank=True,
        help_text="Ixtiyoriy. Shablondagi ikonka to'plamidan kalit.",
    )
    order = models.PositiveSmallIntegerField("tartib", default=0)

    class Meta:
        verbose_name = "janr"
        verbose_name_plural = "janrlar"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("movies:genre_detail", kwargs={"slug": self.slug})


class CategoryQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)


class Category(TimeStampedModel):
    """Janrdan alohida taksonomiya — masalan "Multfilmlar", "Premyeralar",
    "Koreys filmlari". `Movie` va `Series` ikkalasi ham ishlatadi.
    Bosh sahifa bo'limlarini belgilashdan tashqari o'zining public
    sahifasi ham bor (`movies:category_detail`).
    """

    name = models.CharField("nomi", max_length=80, unique=True)
    slug = models.SlugField("slug", max_length=90, unique=True, blank=True)
    description = models.TextField("tavsif", blank=True)
    image = models.ImageField(
        "rasm", upload_to="categories/", blank=True, null=True
    )
    order = models.PositiveSmallIntegerField("tartib", default=0)
    is_active = models.BooleanField("faol", default=True)

    objects = CategoryQuerySet.as_manager()

    class Meta:
        verbose_name = "kategoriya"
        verbose_name_plural = "kategoriyalar"
        ordering = ["order", "name"]
        indexes = [models.Index(fields=["is_active", "order"])]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("movies:category_detail", kwargs={"slug": self.slug})


class Country(TimeStampedModel):
    """Ishlab chiqarilgan davlat — filtr uchun."""

    name = models.CharField("nomi", max_length=100, unique=True)
    code = models.CharField("ISO kodi", max_length=3, blank=True)
    slug = models.SlugField("slug", max_length=110, unique=True, blank=True)

    class Meta:
        verbose_name = "davlat"
        verbose_name_plural = "davlatlar"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name)
        super().save(*args, **kwargs)


class Language(TimeStampedModel):
    """Film tili — filtr uchun."""

    name = models.CharField("nomi", max_length=100, unique=True)
    code = models.CharField("kod", max_length=8, blank=True)
    slug = models.SlugField("slug", max_length=110, unique=True, blank=True)

    class Meta:
        verbose_name = "til"
        verbose_name_plural = "tillar"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name)
        super().save(*args, **kwargs)


class Director(TimeStampedModel):
    """Film/serial rejissyori."""

    full_name = models.CharField("to'liq ism", max_length=150)
    slug = models.SlugField("slug", max_length=160, unique=True, blank=True)
    photo = models.ImageField("surat", upload_to="directors/", blank=True, null=True)
    bio = models.TextField("qisqacha", blank=True)

    class Meta:
        verbose_name = "rejissyor"
        verbose_name_plural = "rejissyorlar"
        ordering = ["full_name"]
        indexes = [models.Index(fields=["full_name"])]

    def __str__(self):
        return self.full_name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.full_name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("movies:director_detail", kwargs={"slug": self.slug})

    @property
    def initials(self):
        parts = [p for p in self.full_name.split() if p]
        if not parts:
            return "?"
        if len(parts) == 1:
            return parts[0][:2].upper()
        return (parts[0][0] + parts[-1][0]).upper()


class Actor(TimeStampedModel):
    """Film/serialda o'ynagan aktyor."""

    full_name = models.CharField("to'liq ism", max_length=150)
    slug = models.SlugField("slug", max_length=160, unique=True, blank=True)
    photo = models.ImageField("surat", upload_to="actors/", blank=True, null=True)
    bio = models.TextField("qisqacha", blank=True)

    class Meta:
        verbose_name = "aktyor"
        verbose_name_plural = "aktyorlar"
        ordering = ["full_name"]
        indexes = [models.Index(fields=["full_name"])]

    def __str__(self):
        return self.full_name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.full_name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("movies:actor_detail", kwargs={"slug": self.slug})

    @property
    def initials(self):
        parts = [p for p in self.full_name.split() if p]
        if not parts:
            return "?"
        if len(parts) == 1:
            return parts[0][:2].upper()
        return (parts[0][0] + parts[-1][0]).upper()


# ---------------------------------------------------------------------------
# Film
# ---------------------------------------------------------------------------


class MovieQuerySet(models.QuerySet):
    """Ko'p takrorlanadigan so'rovlarni bitta joyda saqlaymiz."""

    def published(self):
        return self.filter(is_published=True)

    def with_relations(self):
        """N+1 so'rovlarning oldini oladi — kartalar va ro'yxatlar uchun."""
        return self.select_related("country", "language", "director").prefetch_related(
            "genres"
        )

    def trending(self):
        """Oxirgi qo'shilganlar orasidan eng ko'p ko'rilganlari."""
        return self.published().with_relations().order_by("-views_count", "-created_at")

    def newest(self):
        return self.published().with_relations().order_by("-created_at")

    def top_rated(self):
        return (
            self.published()
            .with_relations()
            .filter(rating_count__gt=0)
            .order_by("-avg_rating", "-rating_count")
        )

    def featured(self):
        return self.published().with_relations().filter(is_featured=True)

    def trending_flagged(self):
        """Admin qo'lda "trendda" deb belgilagan filmlar.

        `trending()` dan ATAYLAB alohida — `trending()` bosh sahifadagi
        "Trending"/"Popular" bo'limlarini ko'rishlar soni bo'yicha quradi
        va shu holicha qoladi. Bu metod kelajakda admin tanlovi bilan
        ishlaydigan alohida bo'lim uchun (masalan qo'shimcha bo'lim).
        """
        return self.published().with_relations().filter(is_trending=True)


class Movie(TimeStampedModel):
    """Katalogdagi bitta film."""

    class Quality(models.TextChoices):
        SD = "SD", "SD"
        HD = "HD", "HD 720p"
        FULL_HD = "FHD", "Full HD 1080p"
        UHD = "4K", "4K Ultra HD"

    class LicenseType(models.TextChoices):
        """Kontentning huquqiy holati — ko'rish/yuklash ruxsatini belgilaydi."""

        PUBLIC_DOMAIN = "public_domain", "Public domain / Creative Commons"
        LICENSED = "licensed", "Litsenziyalangan (huquq egasi ruxsati bor)"
        TRAILER_ONLY = "trailer_only", "Faqat treyler (to'liq film yo'q)"

    # --- Matn ---
    title = models.CharField("sarlavha", max_length=200)
    original_title = models.CharField("original sarlavha", max_length=200, blank=True)
    slug = models.SlugField("slug", max_length=220, unique=True, blank=True)
    description = models.TextField("tavsif")
    short_description = models.CharField(
        "qisqa tavsif",
        max_length=300,
        blank=True,
        help_text="Kartalar va hero bo'limida ko'rsatiladi. Bo'sh bo'lsa tavsifdan olinadi.",
    )
    meta_description = models.CharField(
        "SEO meta description",
        max_length=170,
        blank=True,
        help_text="Qidiruv tizimlari uchun. Bo'sh bo'lsa qisqa tavsif ishlatiladi.",
    )

    # --- Media ---
    poster = models.ImageField(
        "poster", upload_to="posters/%Y/%m/", blank=True, null=True,
        help_text="Vertikal (2:3), masalan 500x750.",
    )
    backdrop = models.ImageField(
        "backdrop", upload_to="backdrops/%Y/%m/", blank=True, null=True,
        help_text="Gorizontal (16:9), hero va detail sahifasi foni uchun.",
    )
    trailer_url = models.URLField(
        "treyler havolasi", blank=True,
        help_text="YouTube/Vimeo embed havolasi.",
    )
    video_url = models.URLField(
        "video havolasi", blank=True,
        help_text="To'g'ridan-to'g'ri MP4/HLS havolasi (qonuniy manba).",
    )
    video_file = models.FileField(
        "video fayl", upload_to="videos/%Y/%m/", blank=True, null=True,
        help_text="Serverga yuklangan qonuniy video. video_url dan ustun turadi.",
    )
    download_url = models.URLField(
        "yuklab olish havolasi", blank=True, null=True,
        help_text="Faqat huquq egasi ruxsat bergan fayl havolasi.",
    )

    # --- Meta ---
    release_year = models.PositiveSmallIntegerField(
        "chiqarilgan yil",
        validators=[MinValueValidator(1888), MaxValueValidator(2100)],
    )
    release_date = models.DateField(
        "chiqarilgan sana", null=True, blank=True,
        help_text="Aniq sana ma'lum bo'lsa. Yil maydoni asosiy bo'lib qoladi.",
    )
    duration_minutes = models.PositiveSmallIntegerField("davomiyligi (daqiqa)", default=0)
    quality = models.CharField(
        "sifat", max_length=4, choices=Quality.choices, default=Quality.HD
    )
    age_rating = models.CharField(
        "yosh chegarasi", max_length=4, choices=AgeRating.choices, blank=True, default="",
    )
    imdb_rating = models.DecimalField(
        "IMDb reytingi",
        max_digits=3, decimal_places=1, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Tashqi manba reytingi (0-10). Foydalanuvchi reytingidan alohida.",
    )

    # --- Aloqalar ---
    genres = models.ManyToManyField(Genre, related_name="movies", verbose_name="janrlar")
    categories = models.ManyToManyField(
        Category, related_name="movies", blank=True, verbose_name="kategoriyalar",
    )
    country = models.ForeignKey(
        Country, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="movies", verbose_name="davlat",
    )
    language = models.ForeignKey(
        Language, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="movies", verbose_name="til",
    )
    director = models.ForeignKey(
        Director, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="directed_movies", verbose_name="rejissyor",
    )
    cast = models.ManyToManyField(
        Actor, through="MovieCast", related_name="acted_movies",
        blank=True, verbose_name="aktyorlar",
    )

    # --- Huquqiy holat ---
    license_type = models.CharField(
        "litsenziya turi",
        max_length=20,
        choices=LicenseType.choices,
        default=LicenseType.TRAILER_ONLY,
        help_text="Kontentning huquqiy holati. Ko'rish va yuklash shunga qarab ochiladi.",
    )
    license_note = models.CharField(
        "litsenziya izohi", max_length=200, blank=True,
        help_text="Masalan: 'CC BY 3.0, Blender Foundation'.",
    )
    is_download_allowed = models.BooleanField(
        "yuklab olishga ruxsat", default=False,
        help_text="Faqat huquq egasi ruxsat bergan fayllar uchun belgilang.",
    )

    # --- Holat ---
    is_featured = models.BooleanField(
        "tanlangan", default=False,
        help_text="Bosh sahifadagi hero va 'Featured' bo'limida ko'rsatiladi.",
    )
    is_trending = models.BooleanField(
        "trendda", default=False,
        help_text="Bosh sahifadagi «Trend» bo'limiga qo'lda qo'shish.",
    )
    is_premium = models.BooleanField(
        "premium", default=False,
        help_text="Faqat premium foydalanuvchilar uchun (hozircha belgi sifatida).",
    )
    is_published = models.BooleanField(
        "chop etilgan", default=False,
        help_text="Belgilanmagan bo'lsa film saytda ko'rinmaydi.",
    )
    views_count = models.PositiveIntegerField("ko'rishlar soni", default=0, editable=False)
    downloads_count = models.PositiveIntegerField(
        "yuklab olishlar soni", default=0, editable=False,
    )

    # --- Denormalizatsiya ---
    # Har detail sahifada AVG() hisoblamaslik uchun Rating saqlanganda yangilanadi.
    avg_rating = models.DecimalField(
        "o'rtacha reyting", max_digits=3, decimal_places=2, default=0, editable=False
    )
    rating_count = models.PositiveIntegerField("baholar soni", default=0, editable=False)

    objects = MovieQuerySet.as_manager()

    class Meta:
        verbose_name = "film"
        verbose_name_plural = "filmlar"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_published", "-created_at"]),
            models.Index(fields=["is_published", "-views_count"]),
            models.Index(fields=["is_published", "-avg_rating"]),
            models.Index(fields=["is_published", "is_featured"]),
            models.Index(fields=["is_published", "is_trending"]),
            models.Index(fields=["is_published", "is_premium"]),
            models.Index(fields=["release_year"]),
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

    # --- URL lar ---

    def get_absolute_url(self):
        return reverse("movies:movie_detail", kwargs={"slug": self.slug})

    def get_watch_url(self):
        """Pleer endi mustaqil sahifa emas — film detali sahifasining
        o'zida (`#player` bo'limida) joylashgan."""
        return f"{self.get_absolute_url()}#player"

    # --- Huquqiy tekshiruvlar ---

    @property
    def has_video_source(self):
        return bool(self.video_file or self.video_url)

    @property
    def can_watch(self):
        """To'liq filmni ko'rish mumkinmi?

        Faqat public domain yoki litsenziyalangan kontent uchun va video
        manbasi mavjud bo'lganda True.
        """
        return (
            self.license_type
            in {self.LicenseType.PUBLIC_DOMAIN, self.LicenseType.LICENSED}
            and self.has_video_source
        )

    @property
    def can_download(self):
        """Yuklab olish tugmasi ko'rsatilsinmi?

        Uch shart birdan bajarilishi kerak: litsenziya ruxsat beradi,
        administrator alohida ruxsat bergan va havola mavjud.
        """
        return (
            self.license_type
            in {self.LicenseType.PUBLIC_DOMAIN, self.LicenseType.LICENSED}
            and self.is_download_allowed
            and bool(self.download_url)
        )

    @property
    def video_source(self):
        """Player uchun yakuniy video manba (yuklangan fayl ustun turadi)."""
        if self.video_file:
            return self.video_file.url
        return self.video_url or ""

    # --- Ko'rsatish uchun yordamchilar ---

    @property
    def release_display(self):
        """Aniq sana bo'lsa uni, aks holda yilni qaytaradi."""
        return self.release_date or self.release_year

    @property
    def duration_display(self):
        """95 -> '1s 35d'."""
        if not self.duration_minutes:
            return "—"
        hours, minutes = divmod(self.duration_minutes, 60)
        if hours and minutes:
            return f"{hours}s {minutes}d"
        if hours:
            return f"{hours}s"
        return f"{minutes}d"

    @property
    def display_rating(self):
        """Kartalarda ko'rsatiladigan reyting: foydalanuvchi bahosi ustun."""
        if self.rating_count:
            # 1-5 shkalasini 10 ballikka keltiramiz.
            return round(float(self.avg_rating) * 2, 1)
        return float(self.imdb_rating)

    @property
    def meta_description_text(self):
        return self.meta_description or self.short_description

    def recalculate_rating(self):
        """Reyting o'rtachasini qayta hisoblab, denormalizatsiya maydonlarini yangilaydi.

        reviews.Rating modelidan save()/delete() da chaqiriladi.
        """
        from django.db.models import Avg, Count

        stats = self.ratings.aggregate(average=Avg("score"), total=Count("id"))
        self.avg_rating = round(stats["average"] or 0, 2)
        self.rating_count = stats["total"] or 0
        # update_fields — faqat shu ikki ustun yoziladi, save() signal zanjiri qisqaradi.
        Movie.objects.filter(pk=self.pk).update(
            avg_rating=self.avg_rating, rating_count=self.rating_count
        )


class MovieCast(models.Model):
    """Film va aktyor orasidagi bog'lovchi jadval (rol nomi bilan)."""

    movie = models.ForeignKey(
        Movie, on_delete=models.CASCADE, related_name="cast_members", verbose_name="film"
    )
    actor = models.ForeignKey(
        Actor, on_delete=models.CASCADE, related_name="roles", verbose_name="aktyor"
    )
    character_name = models.CharField("rol nomi", max_length=150, blank=True)
    order = models.PositiveSmallIntegerField("tartib", default=0)

    class Meta:
        verbose_name = "aktyor roli"
        verbose_name_plural = "aktyorlar tarkibi"
        ordering = ["order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["movie", "actor"], name="unique_movie_actor_role"
            )
        ]

    def __str__(self):
        if self.character_name:
            return f"{self.actor} — {self.character_name}"
        return str(self.actor)


class Screenshot(models.Model):
    """Film detail sahifasidagi kadrlar galereyasi."""

    movie = models.ForeignKey(
        Movie, on_delete=models.CASCADE, related_name="screenshots", verbose_name="film"
    )
    image = models.ImageField("rasm", upload_to="screenshots/%Y/%m/")
    caption = models.CharField("izoh", max_length=150, blank=True)
    order = models.PositiveSmallIntegerField("tartib", default=0)

    class Meta:
        verbose_name = "kadr"
        verbose_name_plural = "kadrlar"
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.movie.title} — kadr {self.order}"


# ---------------------------------------------------------------------------
# Foydalanuvchi va film orasidagi aloqalar
# ---------------------------------------------------------------------------


class Watchlist(models.Model):
    """Keyinroq ko'rish uchun saqlangan filmlar."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="watchlist_items", verbose_name="foydalanuvchi",
    )
    movie = models.ForeignKey(
        Movie, on_delete=models.CASCADE, related_name="watchlist_entries", verbose_name="film"
    )
    added_at = models.DateTimeField("qo'shilgan", auto_now_add=True)

    class Meta:
        verbose_name = "watchlist elementi"
        verbose_name_plural = "watchlist"
        ordering = ["-added_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "movie"], name="unique_watchlist_entry")
        ]

    def __str__(self):
        return f"{self.user} → {self.movie}"


class Favorite(models.Model):
    """Sevimli filmlar (yurak tugmasi)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="favorite_items", verbose_name="foydalanuvchi",
    )
    movie = models.ForeignKey(
        Movie, on_delete=models.CASCADE, related_name="favorite_entries", verbose_name="film"
    )
    added_at = models.DateTimeField("qo'shilgan", auto_now_add=True)

    class Meta:
        verbose_name = "sevimli"
        verbose_name_plural = "sevimlilar"
        ordering = ["-added_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "movie"], name="unique_favorite_entry")
        ]

    def __str__(self):
        return f"{self.user} ♥ {self.movie}"


class ViewHistory(models.Model):
    """Ko'rish tarixi va to'xtatilgan joy.

    Har (user, movie) juftligi uchun bitta yozuv — player davomiylikni
    shu yerga yozadi, keyin "Davom ettirish" imkonini beradi.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="view_history", verbose_name="foydalanuvchi",
    )
    movie = models.ForeignKey(
        Movie, on_delete=models.CASCADE, related_name="view_entries", verbose_name="film"
    )
    progress_seconds = models.PositiveIntegerField("to'xtagan joy (soniya)", default=0)
    is_finished = models.BooleanField("tugatilgan", default=False)
    watched_at = models.DateTimeField("oxirgi ko'rish", auto_now=True)
    created_at = models.DateTimeField("birinchi ko'rish", auto_now_add=True)

    class Meta:
        verbose_name = "ko'rish tarixi"
        verbose_name_plural = "ko'rish tarixi"
        ordering = ["-watched_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "movie"], name="unique_view_history_entry")
        ]
        indexes = [models.Index(fields=["-watched_at"])]

    def __str__(self):
        return f"{self.user} — {self.movie} ({self.progress_seconds}s)"

    @property
    def progress_percent(self):
        """Progress barni chizish uchun 0-100 oralig'idagi qiymat."""
        total = self.movie.duration_minutes * 60
        if not total:
            return 0
        return min(100, round(self.progress_seconds / total * 100))
