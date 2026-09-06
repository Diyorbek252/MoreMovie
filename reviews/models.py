"""Reyting va sharh modellari."""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Rating(models.Model):
    """Foydalanuvchining filmga bergan bahosi (1-5 yulduz).

    UniqueConstraint tufayli bitta foydalanuvchi bitta filmga faqat bitta
    baho bera oladi — qayta baholasa, mavjud yozuv yangilanadi.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="ratings", verbose_name="foydalanuvchi",
    )
    movie = models.ForeignKey(
        "movies.Movie", on_delete=models.CASCADE,
        related_name="ratings", verbose_name="film",
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
            models.UniqueConstraint(fields=["user", "movie"], name="unique_user_movie_rating")
        ]

    def __str__(self):
        return f"{self.user} → {self.movie}: {self.score}/5"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Filmning o'rtacha reytingini yangilaymiz (denormalizatsiya).
        self.movie.recalculate_rating()

    def delete(self, *args, **kwargs):
        movie = self.movie
        super().delete(*args, **kwargs)
        movie.recalculate_rating()


class Review(models.Model):
    """Foydalanuvchi sharhi. Saytda faqat tasdiqlangan sharhlar ko'rinadi."""

    class Status(models.TextChoices):
        PENDING = "pending", "Moderatsiyada"
        APPROVED = "approved", "Tasdiqlangan"
        REJECTED = "rejected", "Rad etilgan"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="reviews", verbose_name="foydalanuvchi",
    )
    movie = models.ForeignKey(
        "movies.Movie", on_delete=models.CASCADE,
        related_name="reviews", verbose_name="film",
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
            models.UniqueConstraint(fields=["user", "movie"], name="unique_user_movie_review")
        ]
        indexes = [models.Index(fields=["status", "-created_at"])]

    def __str__(self):
        return f"{self.user} — {self.movie} ({self.get_status_display()})"

    @property
    def is_visible(self):
        return self.status == self.Status.APPROVED

    @property
    def user_score(self):
        """Sharh yonida ko'rsatish uchun shu foydalanuvchining shu filmga bahosi."""
        rating = Rating.objects.filter(user=self.user, movie=self.movie).first()
        return rating.score if rating else None
