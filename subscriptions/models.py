"""Obuna tizimi — rejalar, muddat narxlari va foydalanuvchi obunalari.

To'lov haqiqiy pulda amalga oshiriladi va admin tomonidan QO'LDA
tasdiqlanadi: foydalanuvchi karta o'tkazmasi qilib chek skrinshotini
yuklaydi, so'rov `PENDING` holatida dashboard'ga tushadi, admin uni
tasdiqlagach obuna faollashadi (qarang: ``subscriptions.services``).

Obunaning asosiy huquqi — `Movie.is_premium` belgilangan filmlarni
ko'rish. MUHIM: bu huquq litsenziya tekshiruvidan (`Movie.can_watch`)
KEYIN qo'llaniladi, uning o'rniga emas — litsenziya ruxsat bermagan
filmni hech qanday obuna ocha olmaydi.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone

from movies.models import TimeStampedModel, unique_slugify


class Plan(TimeStampedModel):
    """Obuna darajasi — masalan "Standart" yoki "Premium".

    Rejalar kodda hardcode qilinmaydi, admin dashboard'dan yaratadi.

    Ikki xil "imkoniyat" tushunchasini ATAYLAB ajratamiz:

    - ``allows_premium_movies`` / ``has_badge`` / ``is_ad_free`` —
      haqiqiy huquqlar, kod shularni tekshiradi;
    - ``features`` — faqat narxlar kartasida ko'rsatiladigan marketing
      matni. Bu yerga yozilgan gap o'z-o'zidan hech narsani ochmaydi.
    """

    name = models.CharField("nomi", max_length=150)
    slug = models.SlugField("slug", max_length=160, unique=True, blank=True)
    tagline = models.CharField(
        "qisqa shior", max_length=200, blank=True,
        help_text="Kartada nom ostida chiqadi. Masalan: «Eng ommabop tanlov».",
    )
    description = models.TextField("tavsif", blank=True)
    features = models.TextField(
        "imkoniyatlar ro'yxati", blank=True,
        help_text=(
            "Har qatorda bitta imkoniyat — kartada ✓ belgisi bilan chiqadi. "
            "DIQQAT: bu faqat ko'rsatish uchun, huquqlarni quyidagi "
            "belgilar boshqaradi."
        ),
    )

    level = models.PositiveSmallIntegerField(
        "daraja", default=1,
        help_text="Rejalarni taqqoslash uchun — raqam qancha katta bo'lsa, reja shuncha yuqori.",
    )

    # --- Haqiqiy huquqlar ---
    allows_premium_movies = models.BooleanField(
        "premium filmlarni ochadi", default=True,
        help_text="Belgilansa, obunachi «premium» deb belgilangan filmlarni ko'ra oladi.",
    )
    has_badge = models.BooleanField(
        "nishon beradi", default=True,
        help_text="Profil va sharhlarda oltin «Premium» nishoni ko'rsatiladi.",
    )
    is_ad_free = models.BooleanField(
        "reklamasiz", default=True,
        help_text="Kelajakdagi reklama bloklari bu obunachilarga ko'rsatilmaydi.",
    )

    # --- Ko'rinish ---
    is_highlighted = models.BooleanField(
        "ajratib ko'rsatilsin", default=False,
        help_text="Narxlar sahifasida ko'tarilgan holda, «Eng ommabop» lentasi bilan chiqadi.",
    )
    is_active = models.BooleanField("faol", default=True)
    order = models.PositiveSmallIntegerField("tartib", default=0)

    class Meta:
        verbose_name = "obuna rejasi"
        verbose_name_plural = "obuna rejalari"
        ordering = ["order", "level"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name)
        super().save(*args, **kwargs)

    @property
    def feature_list(self):
        """`features` matnini kartada aylanish uchun qatorlarga ajratadi."""
        return [line.strip() for line in self.features.splitlines() if line.strip()]

    @property
    def cheapest_price(self):
        """Kartada «... so'mdan boshlab» deb ko'rsatish uchun.

        `prices.all()` ataylab — ro'yxat view'i `prefetch_related("prices")`
        qilgani uchun qo'shimcha so'rov yuzaga kelmaydi.
        """
        active = [price for price in self.prices.all() if price.is_active]
        return min(active, key=lambda price: price.price) if active else None


class PlanPrice(models.Model):
    """Reja uchun muddat varianti — 1 oy, 3 oy, 1 yil.

    Narx butun sonda (so'mda) saqlanadi: bu miqdorlarda tiyin amalda
    ishlatilmaydi, shuning uchun Decimal murakkabligi keraksiz.
    """

    plan = models.ForeignKey(
        Plan, on_delete=models.CASCADE, related_name="prices", verbose_name="reja"
    )
    label = models.CharField("muddat nomi", max_length=60, help_text="Masalan: «3 oy».")
    duration_days = models.PositiveIntegerField(
        "muddat (kun)", help_text="Masalan: 30, 90, 365."
    )
    price = models.PositiveIntegerField("narx (so'm)")
    old_price = models.PositiveIntegerField(
        "eski narx (so'm)", null=True, blank=True,
        help_text="To'ldirilsa, chegirmani ko'rsatish uchun ustidan chizilgan holda chiqadi.",
    )
    is_active = models.BooleanField("faol", default=True)
    order = models.PositiveSmallIntegerField("tartib", default=0)

    class Meta:
        verbose_name = "muddat narxi"
        verbose_name_plural = "muddat narxlari"
        ordering = ["order", "duration_days"]

    def __str__(self):
        return f"{self.plan.name} — {self.label}"

    @property
    def monthly_equivalent(self):
        """«Oyiga ~X so'm» — uzoq muddatning foydasini ko'rsatish uchun."""
        months = self.duration_days / 30
        return round(self.price / months) if months else self.price

    @property
    def discount_percent(self):
        """Eski narxga nisbatan chegirma foizi (eski narx bo'lmasa 0)."""
        if not self.old_price or self.old_price <= self.price:
            return 0
        return round((self.old_price - self.price) / self.old_price * 100)


class Subscription(TimeStampedModel):
    """Foydalanuvchining obuna so'rovi va (tasdiqlangach) huquqi.

    Bitta jadval ikkala rolni bajaradi: `PENDING` holatida bu hali
    to'lov tasdig'ini kutayotgan so'rov, `ACTIVE` holatida esa amal
    qilayotgan obuna. Shu bilan foydalanuvchining to'liq tarixi bitta
    joyda qoladi.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Tasdiq kutilmoqda"
        ACTIVE = "active", "Faol"
        REJECTED = "rejected", "Rad etilgan"
        EXPIRED = "expired", "Muddati tugagan"
        CANCELLED = "cancelled", "Bekor qilingan"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="subscriptions", verbose_name="foydalanuvchi",
    )
    # PROTECT — shop.Order.product bilan bir xil sabab: reja o'chirilsa ham
    # to'lov tarixi yo'qolmasligi kerak.
    plan = models.ForeignKey(
        Plan, on_delete=models.PROTECT,
        related_name="subscriptions", verbose_name="reja",
    )

    # Xarid vaqtidagi qiymatlar — reja keyin tahrirlansa ham tarix o'zgarmaydi.
    plan_name = models.CharField("reja nomi", max_length=150)
    duration_days = models.PositiveIntegerField("muddat (kun)")
    price_paid = models.PositiveIntegerField("to'langan summa (so'm)")

    status = models.CharField(
        "holat", max_length=10, choices=Status.choices, default=Status.PENDING
    )

    # --- To'lov isboti (foydalanuvchi to'ldiradi) ---
    payment_note = models.CharField(
        "to'lov haqida", max_length=200, blank=True,
        help_text="Masalan: karta oxirgi 4 raqami va o'tkazma vaqti.",
    )
    payment_receipt = models.ImageField(
        "to'lov cheki", upload_to="subscriptions/%Y/%m/", blank=True, null=True,
        help_text="O'tkazma skrinshoti — admin shuni tekshiradi.",
    )

    # --- Muddat (tasdiqlangunga qadar bo'sh) ---
    starts_at = models.DateTimeField("boshlanish vaqti", null=True, blank=True)
    ends_at = models.DateTimeField("tugash vaqti", null=True, blank=True)

    # --- Moderatsiya ---
    admin_note = models.CharField(
        "admin izohi", max_length=200, blank=True,
        help_text="Rad etilganda foydalanuvchiga sabab sifatida yuboriladi.",
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="+", verbose_name="tekshirgan admin",
    )
    reviewed_at = models.DateTimeField("tekshirilgan vaqti", null=True, blank=True)

    class Meta:
        verbose_name = "obuna"
        verbose_name_plural = "obunalar"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.user} — {self.plan_name} ({self.get_status_display()})"

    @property
    def is_currently_active(self):
        """Hozir amal qilyaptimi?

        Muddat tekshiruvi shu yerda — `status` ustuni eskirgan bo'lsa ham
        (masalan `expire_subscriptions` komandasi ishlamay qolgan bo'lsa)
        muddati o'tgan obuna huquq bermaydi.
        """
        return (
            self.status == self.Status.ACTIVE
            and self.ends_at is not None
            and self.ends_at > timezone.now()
        )

    @property
    def days_left(self):
        """Tugashiga necha kun qolgani (tugagan yoki faol bo'lmasa 0)."""
        if not self.is_currently_active:
            return 0
        return max(0, (self.ends_at - timezone.now()).days)

    @property
    def percent_left(self):
        """Qolgan muddat foizi (0-100) — "Mening obunam" sahifasidagi
        progress chizig'i uchun."""
        if not self.is_currently_active or not self.starts_at:
            return 0
        total = (self.ends_at - self.starts_at).total_seconds()
        if total <= 0:
            return 0
        left = (self.ends_at - timezone.now()).total_seconds()
        return max(0, min(100, round(left / total * 100)))
