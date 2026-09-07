"""Cinepoint do'koni — mahsulotlar, buyurtmalar va balans tranzaksiyalari.

Har bir foydalanuvchining balansi ``users.Profile.balance`` maydonida
saqlanadi (User yaratilganda avtomatik kafolatlangan profil orqali).
Balans hech qachon to'g'ridan-to'g'ri o'zgartirilmaydi — faqat
``shop.services.adjust_balance()`` orqali, shu bilan har bir o'zgarish
``CinepointTransaction`` jadvalida audit uchun qoladi.
"""

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from movies.models import TimeStampedModel, unique_slugify


class Product(TimeStampedModel):
    """Do'kondagi mahsulot — cinepointga sotib olinadi."""

    name = models.CharField("nomi", max_length=150)
    slug = models.SlugField("slug", max_length=160, unique=True, blank=True)
    description = models.TextField("tavsif", blank=True)
    image = models.ImageField("rasm", upload_to="shop/%Y/%m/", blank=True, null=True)
    price = models.PositiveIntegerField("narx (cinepoint)")
    stock = models.PositiveIntegerField(
        "zaxira",
        null=True,
        blank=True,
        help_text="Bo'sh qoldirilsa — cheksiz zaxira.",
    )
    is_active = models.BooleanField("faol", default=True)
    order = models.PositiveSmallIntegerField("tartib", default=0)

    class Meta:
        verbose_name = "mahsulot"
        verbose_name_plural = "mahsulotlar"
        ordering = ["order", "-created_at"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name)
        super().save(*args, **kwargs)

    @property
    def is_in_stock(self):
        """Zaxira cheklanmagan yoki hali qolgan bo'lsa True."""
        return self.stock is None or self.stock > 0


class Order(TimeStampedModel):
    """Foydalanuvchining mahsulot xaridi — admin qo'lda yetkazib beradi."""

    class Status(models.TextChoices):
        PENDING = "pending", "Kutilmoqda"
        DELIVERED = "delivered", "Yetkazildi"
        CANCELLED = "cancelled", "Bekor qilindi"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="shop_orders", verbose_name="foydalanuvchi",
    )
    # PROTECT — boshqa hamma joyda CASCADE ishlatiladi, lekin bu yerda
    # moliyaviy tarixni saqlash muhimroq: mahsulot o'chirilsa ham
    # foydalanuvchining xarid tarixi yo'qolmasligi kerak.
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT,
        related_name="orders", verbose_name="mahsulot",
    )
    # Xarid vaqtidagi nomi/narxi — mahsulot keyin tahrirlansa yoki
    # o'chirilsa ham tarix o'zgarmas qoladi.
    product_name = models.CharField("mahsulot nomi", max_length=150)
    quantity = models.PositiveIntegerField("miqdor", default=1)
    # Umumiy summa (bir dona narxi emas) — bekor qilinganda to'liq shu
    # summa qaytariladi, quantity bilan qayta ko'paytirish shart emas.
    price_paid = models.PositiveIntegerField("to'langan narx (cinepoint, umumiy)")
    status = models.CharField(
        "holat", max_length=10, choices=Status.choices, default=Status.PENDING
    )
    admin_note = models.CharField(
        "admin izohi", max_length=200, blank=True,
        help_text="Ichki foydalanish uchun — foydalanuvchiga ko'rinmaydi.",
    )
    delivered_at = models.DateTimeField("yetkazilgan vaqti", null=True, blank=True)

    class Meta:
        verbose_name = "buyurtma"
        verbose_name_plural = "buyurtmalar"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "-created_at"])]

    def __str__(self):
        return f"{self.user} — {self.product_name} ({self.get_status_display()})"


class CinepointTransaction(models.Model):
    """Balans o'zgarishlarining o'zgarmas tarixi (ledger).

    Har qanday balans o'zgarishi — admin tuzatishi, avtomatik mukofot,
    xarid yoki qaytarish — shu yerda bitta yozuv qoldiradi. `content_object`
    orqali qaysi obyekt (Movie/Review/Order) sabab bo'lganini bilish va
    bir xil mukofotning ikki marta berilmasligini tekshirish mumkin
    (qarang: ``shop.services.has_earned``).
    """

    class Reason(models.TextChoices):
        ADMIN_ADJUST = "admin", "Admin tomonidan"
        MOVIE_WATCH = "movie_watch", "Film ko'rish"
        REVIEW_APPROVED = "review_approved", "Sharh tasdiqlandi"
        PURCHASE = "purchase", "Xarid"
        REFUND = "refund", "Qaytarish"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="cinepoint_transactions", verbose_name="foydalanuvchi",
    )
    amount = models.IntegerField(
        "miqdor", help_text="Kredit uchun musbat, debet uchun manfiy son."
    )
    reason = models.CharField("sabab", max_length=20, choices=Reason.choices)
    note = models.CharField("izoh", max_length=255, blank=True)

    # Generic FK — dashboard.ActivityLog bilan bir xil naqsh.
    content_type = models.ForeignKey(
        ContentType, on_delete=models.SET_NULL, null=True, blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="+",
        verbose_name="qo'lda o'zgartirgan admin",
    )
    created_at = models.DateTimeField("yaratilgan", auto_now_add=True)

    class Meta:
        verbose_name = "cinepoint tranzaksiyasi"
        verbose_name_plural = "cinepoint tranzaksiyalari"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "-created_at"])]

    def __str__(self):
        sign = "+" if self.amount >= 0 else ""
        return f"{self.user} {sign}{self.amount} ({self.get_reason_display()})"
