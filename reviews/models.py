"""Reyting va sharh modellari.

Film HAM serial baholanishi/sharh qoldirilishi mumkin — shuning uchun har
bir yozuvda `movie` va `series` maydonlaridan ANIQ BITTASI to'ldiriladi
(ikkalasi ham emas, hech biri ham emas). Alohida `MovieRating`/`SeriesRating`
modellari yaratish o'rniga shu yo'l tanlandi: moderatsiya navbati, o'rtacha
reyting hisoblash mantiqi va dashboard sahifasi ikkalasi uchun ham BITTA
bo'lib qoladi — kod ikki marta yozilmaydi.
"""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Rating(models.Model):
    """Foydalanuvchining film yoki serialga bergan bahosi (1-5 yulduz).

    UniqueConstraint tufayli bitta foydalanuvchi bitta filmga/serialga
    faqat bitta baho bera oladi — qayta baholasa, mavjud yozuv yangilanadi.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="ratings", verbose_name="foydalanuvchi",
    )
    movie = models.ForeignKey(
        "movies.Movie", on_delete=models.CASCADE, null=True, blank=True,
        related_name="ratings", verbose_name="film",
    )
    series = models.ForeignKey(
        "series.Series", on_delete=models.CASCADE, null=True, blank=True,
        related_name="ratings", verbose_name="serial",
    )
    score = models.PositiveSmallIntegerField(
        "baho",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    created_at = models.DateTimeField("yaratilgan", auto_now_add=True)
    updated_at = models.DateTimeField("yangilangan", auto_now=True)

    class Meta:
        verbose_name = "reyting"
        verbose_name_plural = "reytinglar"
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "movie"], name="unique_user_movie_rating"),
            models.UniqueConstraint(fields=["user", "series"], name="unique_user_series_rating"),
            models.CheckConstraint(
                condition=(
                    models.Q(movie__isnull=False, series__isnull=True)
                    | models.Q(movie__isnull=True, series__isnull=False)
                ),
                name="rating_exactly_one_target",
            ),
        ]

    def __str__(self):
        return f"{self.user} → {self.target}: {self.score}/5"

    @property
    def target(self):
        """Baho qaysi obyektga tegishli — film yoki serial."""
        return self.movie or self.series

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Denormalizatsiya — target'ning o'rtacha reytingini yangilaymiz.
        self.target.recalculate_rating()

    def delete(self, *args, **kwargs):
        target = self.target
        super().delete(*args, **kwargs)
        target.recalculate_rating()


class Review(models.Model):
    """Foydalanuvchi sharhi. Saytda faqat tasdiqlangan sharhlar ko'rinadi."""

    class Status(models.TextChoices):
        PENDING = "pending", "Moderatsiyada"
        APPROVED = "approved", "Tasdiqlangan"
        REJECTED = "rejected", "Rad etilgan"
        REPORTED = "reported", "Shikoyat qilingan"
        SPAM = "spam", "Spam"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="reviews", verbose_name="foydalanuvchi",
    )
    movie = models.ForeignKey(
        "movies.Movie", on_delete=models.CASCADE, null=True, blank=True,
        related_name="reviews", verbose_name="film",
    )
    series = models.ForeignKey(
        "series.Series", on_delete=models.CASCADE, null=True, blank=True,
        related_name="reviews", verbose_name="serial",
    )
    comment = models.TextField("sharh", max_length=2000)
    status = models.CharField(
        "holat", max_length=10, choices=Status.choices, default=Status.PENDING
    )
    moderator_note = models.CharField(
        "moderator izohi", max_length=200, blank=True,
        help_text="Ichki foydalanish uchun — saytda ko'rinmaydi.",
    )
    created_at = models.DateTimeField("yaratilgan", auto_now_add=True)
    updated_at = models.DateTimeField("yangilangan", auto_now=True)

    class Meta:
        verbose_name = "sharh"
        verbose_name_plural = "sharhlar"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "movie"], name="unique_user_movie_review"),
            models.UniqueConstraint(fields=["user", "series"], name="unique_user_series_review"),
            models.CheckConstraint(
                condition=(
                    models.Q(movie__isnull=False, series__isnull=True)
                    | models.Q(movie__isnull=True, series__isnull=False)
                ),
                name="review_exactly_one_target",
            ),
        ]
        indexes = [models.Index(fields=["status", "-created_at"])]

    def __str__(self):
        return f"{self.user} — {self.target} ({self.get_status_display()})"

    @property
    def target(self):
        """Sharh qaysi obyektga tegishli — film yoki serial."""
        return self.movie or self.series

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Sharh holati (tasdiqlangan/rad etilgan/h.k.) target'ning o'rtacha
        # reytingiga ta'sir qiladi — faqat tasdiqlangan sharh egalarining
        # bahosi hisoblanadi (Movie/Series.recalculate_rating).
        self.target.recalculate_rating()

    def delete(self, *args, **kwargs):
        target = self.target
        super().delete(*args, **kwargs)
        target.recalculate_rating()

    @property
    def is_visible(self):
        return self.status == self.Status.APPROVED

    @property
    def user_score(self):
        """Sharh yonida ko'rsatish uchun shu foydalanuvchining shu
        film/serialga bahosi."""
        rating = Rating.objects.filter(
            user=self.user, movie=self.movie, series=self.series
        ).first()
        return rating.score if rating else None
