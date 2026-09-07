"""Foydalanuvchi modellari.

Loyihaning boshidanoq custom User ishlatiladi (AUTH_USER_MODEL = "users.User").
Keyinchalik maydon qo'shish kerak bo'lsa, bazani qayta qurishga hojat qolmaydi.
"""

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse


class User(AbstractUser):
    """MORE-MOVIE foydalanuvchisi.

    Django'ning standart User'idan farqi:
    - email majburiy va unikal (login va parol tiklash uchun ishlatiladi);
    - is_blocked — admin foydalanuvchini bloklashi mumkin. Bloklangan foydalanuvchi
      tizimga kira olmaydi va joriy sessiyasi middleware tomonidan tugatiladi.
    """

    email = models.EmailField(
        "email manzili",
        unique=True,
        error_messages={"unique": "Bu email allaqachon ro'yxatdan o'tgan."},
    )
    is_blocked = models.BooleanField(
        "bloklangan",
        default=False,
        help_text="Belgilansa, foydalanuvchi saytga kira olmaydi.",
    )

    # createsuperuser email ham so'rashi uchun.
    REQUIRED_FIELDS = ["email"]

    class Meta:
        verbose_name = "foydalanuvchi"
        verbose_name_plural = "foydalanuvchilar"
        ordering = ["-date_joined"]

    def __str__(self):
        return self.username

    def get_absolute_url(self):
        return reverse("users:profile")

    @property
    def display_name(self):
        """Profilda ko'rsatiladigan ism — to'liq ism bo'lsa o'sha, aks holda username."""
        return self.get_full_name() or self.username

    @property
    def initials(self):
        """Avatar bo'lmaganda ishlatiladigan bosh harflar."""
        source = self.get_full_name() or self.username
        parts = [p for p in source.split() if p]
        if not parts:
            return "?"
        if len(parts) == 1:
            return parts[0][:2].upper()
        return (parts[0][0] + parts[1][0]).upper()


class Profile(models.Model):
    """Foydalanuvchining qo'shimcha ma'lumotlari.

    User yaratilganda post_save signali orqali avtomatik yaratiladi,
    shuning uchun kodda hech qachon Profile.DoesNotExist ni kutish shart emas.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="foydalanuvchi",
    )
    avatar = models.ImageField(
        "avatar",
        upload_to="avatars/%Y/%m/",
        blank=True,
        null=True,
        help_text="Kvadrat rasm tavsiya etiladi (masalan 400x400).",
    )
    bio = models.TextField("bio", max_length=500, blank=True)
    country = models.CharField("davlat", max_length=80, blank=True)
    balance = models.PositiveIntegerField(
        "cinepoint balansi",
        default=0,
        editable=False,
        help_text="Faqat shop.services.adjust_balance() orqali o'zgartiriladi.",
    )
    created_at = models.DateTimeField("yaratilgan", auto_now_add=True)
    updated_at = models.DateTimeField("yangilangan", auto_now=True)

    class Meta:
        verbose_name = "profil"
        verbose_name_plural = "profillar"

    def __str__(self):
        return f"{self.user.username} profili"

    @property
    def avatar_url(self):
        """Avatar bo'lmasa None qaytaradi — shablon bosh harflarni ko'rsatadi."""
        if self.avatar and hasattr(self.avatar, "url"):
            return self.avatar.url
        return None


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    """Har bir yangi User uchun Profile yaratadi."""
    if created:
        Profile.objects.get_or_create(user=instance)
