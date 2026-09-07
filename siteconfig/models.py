"""Sayt darajasidagi konfiguratsiya: umumiy sozlamalar, bosh sahifa
bo'limlari va bannerlar.

Bu ilova ATAYLAB `movies`/`series` dan alohida: bu yerdagi modellar
katalog kontenti emas, sayt infratuzilmasi. `SiteSettings.load()` kesh
orqali o'qiladi — kelajakda public sahifalarga ulanganda har so'rovda
bazaga murojaat qilinmasligi uchun.
"""

from django.conf import settings
from django.core.cache import cache
from django.db import models

SITE_SETTINGS_CACHE_KEY = "site_settings"
SITE_SETTINGS_CACHE_TTL = 3600


class SiteSettings(models.Model):
    """Yagona qatorli (singleton) global sozlamalar.

    ``pk`` doim ``1`` — ``save()`` buni majburlaydi, ``delete()`` esa
    hech narsa qilmaydi, shu bilan yagona qator hech qachon o'chib
    ketmaydi. ``load()`` orqali o'qing, ``SiteSettings.objects.get(...)``
    orqali emas.
    """

    site_name = models.CharField("sayt nomi", max_length=80, default="MORE-MOVIE")
    logo = models.ImageField("logotip", upload_to="site/", blank=True, null=True)
    favicon = models.ImageField("favicon", upload_to="site/", blank=True, null=True)
    site_description = models.TextField("sayt tavsifi", blank=True)

    contact_email = models.EmailField("aloqa uchun email", blank=True)
    telegram = models.URLField("Telegram", blank=True)
    youtube = models.URLField("YouTube", blank=True)
    instagram = models.URLField("Instagram", blank=True)
    facebook = models.URLField("Facebook", blank=True)

    copyright_text = models.CharField("mualliflik huquqi matni", max_length=200, blank=True)

    seo_title = models.CharField("SEO sarlavha", max_length=70, blank=True)
    seo_description = models.CharField("SEO tavsif", max_length=170, blank=True)
    seo_keywords = models.CharField("SEO kalit so'zlar", max_length=255, blank=True)
    google_analytics_id = models.CharField("Google Analytics ID", max_length=40, blank=True)

    maintenance_mode = models.BooleanField(
        "texnik xizmat rejimi", default=False,
        help_text="Yoqilsa, oddiy foydalanuvchilar uchun sayt vaqtincha yopiladi.",
    )
    maintenance_message = models.TextField(
        "texnik xizmat xabari", blank=True,
        help_text="Texnik xizmat rejimida foydalanuvchiga ko'rsatiladigan matn.",
    )

    updated_at = models.DateTimeField("yangilangan", auto_now=True)

    class Meta:
        verbose_name = "sayt sozlamalari"
        verbose_name_plural = "sayt sozlamalari"

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
        cache.delete(SITE_SETTINGS_CACHE_KEY)

    def delete(self, *args, **kwargs):
        """Yagona qator hech qachon o'chirilmaydi."""

    @classmethod
    def load(cls):
        """Keshdan o'qiydi, bo'lmasa bazadan olib keshga yozadi.

        Qator hali mavjud bo'lmasa (masalan yangi o'rnatilgan loyihada)
        avtomatik yaratadi — chaqiruvchi hech qachon ``DoesNotExist``
        bilan ishlashi shart emas. Birinchi yaratilishda ``site_name``
        `.env` dagi ``SITE_NAME`` qiymatidan olinadi (modelning o'z
        ``default="MORE-MOVIE"`` qiymati emas) — shu bilan kimdir
        `.env` da saytni boshqacha nomlagan bo'lsa, bu qator uni
        "MORE-MOVIE" bilan bosib qo'ymaydi.
        """
        settings_obj = cache.get(SITE_SETTINGS_CACHE_KEY)
        if settings_obj is None:
            settings_obj, _ = cls.objects.get_or_create(
                pk=1, defaults={"site_name": settings.SITE_NAME}
            )
            cache.set(SITE_SETTINGS_CACHE_KEY, settings_obj, SITE_SETTINGS_CACHE_TTL)
        return settings_obj


class HomepageSection(models.Model):
    """Bosh sahifadagi bitta bo'lim (Trending, Top Rated va h.k.).

    Admin bo'limlarni yoqib/o'chirib va tartiblab qo'ya oladi. ``key``
    ``unique`` lekin PK emas — shu bilan FK'lar arzon bo'lib qoladi va
    kalitni keyinchalik o'zgartirish oson bo'ladi.
    """

    class Key(models.TextChoices):
        HERO = "hero", "Hero"
        CONTINUE = "continue", "Davom ettirish"
        TRENDING = "trending", "Trend"
        POPULAR = "popular", "Mashhur"
        NEW_RELEASES = "new_releases", "Yangi qo'shilganlar"
        TOP_RATED = "top_rated", "Yuqori reytingli"
        FEATURED = "featured", "Tanlangan"
        GENRES = "genres", "Janrlar"
        CATEGORY = "category", "Kategoriya bo'yicha"

    key = models.CharField("kalit", max_length=20, choices=Key.choices, unique=True)
    title = models.CharField("sarlavha", max_length=100)
    subtitle = models.CharField("kichik sarlavha", max_length=200, blank=True)
    order = models.PositiveSmallIntegerField("tartib", default=0)
    is_active = models.BooleanField("faol", default=True)
    item_limit = models.PositiveSmallIntegerField("elementlar soni", default=14)

    category = models.ForeignKey(
        "movies.Category", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="homepage_sections", verbose_name="kategoriya",
        help_text="Faqat 'Kategoriya bo'yicha' turi uchun.",
    )
    movie = models.ForeignKey(
        "movies.Movie", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="homepage_sections", verbose_name="tanlangan film",
        help_text="Faqat 'Hero' turi uchun — aniq bir filmni belgilash.",
    )

    class Meta:
        verbose_name = "bosh sahifa bo'limi"
        verbose_name_plural = "bosh sahifa bo'limlari"
        ordering = ["order", "id"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Bosh sahifa keshini bo'shatamiz — o'zgarish darhol ko'rinishi uchun
        # (core.views.HomeView "home_sections" nomi bilan 5 daqiqa keshlaydi).
        cache.delete("home_sections")

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        cache.delete("home_sections")


class BannerQuerySet(models.QuerySet):
    def running(self, position=None):
        """Faol va sana oralig'iga to'g'ri keladigan bannerlar."""
        from django.utils import timezone

        now = timezone.now()
        queryset = self.filter(is_active=True).filter(
            models.Q(start_date__isnull=True) | models.Q(start_date__lte=now)
        ).filter(
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=now)
        )
        if position:
            queryset = queryset.filter(position=position)
        return queryset


class Banner(models.Model):
    """Reklama/banner — sana oralig'i va joylashuv bilan."""

    class Position(models.TextChoices):
        HOMEPAGE_HERO = "homepage_hero", "Bosh sahifa — hero"
        HOMEPAGE_BANNER = "homepage_banner", "Bosh sahifa — banner"
        MOVIE_DETAIL = "movie_detail", "Film sahifasi"
        PLAYER = "player", "Player"
        SIDEBAR = "sidebar", "Yon panel"

    title = models.CharField("sarlavha", max_length=150)
    image = models.ImageField("rasm", upload_to="banners/%Y/%m/")
    link = models.URLField("havola", blank=True)
    position = models.CharField(
        "joylashuv", max_length=20, choices=Position.choices, default=Position.HOMEPAGE_BANNER,
    )
    start_date = models.DateTimeField("boshlanish sanasi", null=True, blank=True)
    end_date = models.DateTimeField("tugash sanasi", null=True, blank=True)
    is_active = models.BooleanField("faol", default=True)
    order = models.PositiveSmallIntegerField("tartib", default=0)

    impressions = models.PositiveIntegerField("ko'rsatilishlar", default=0, editable=False)
    clicks = models.PositiveIntegerField("bosilishlar", default=0, editable=False)

    created_at = models.DateTimeField("yaratilgan", auto_now_add=True)
    updated_at = models.DateTimeField("yangilangan", auto_now=True)

    objects = BannerQuerySet.as_manager()

    class Meta:
        verbose_name = "banner"
        verbose_name_plural = "bannerlar"
        ordering = ["position", "order", "-created_at"]
        indexes = [models.Index(fields=["is_active", "position"])]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(end_date__isnull=True)
                    | models.Q(start_date__isnull=True)
                    | models.Q(end_date__gt=models.F("start_date"))
                ),
                name="banner_end_after_start",
            )
        ]

    def __str__(self):
        return f"{self.title} ({self.get_position_display()})"

    @property
    def ctr(self):
        """Click-through rate, foizda."""
        if not self.impressions:
            return 0.0
        return round(self.clicks / self.impressions * 100, 2)

    @property
    def is_running(self):
        from django.utils import timezone

        if not self.is_active:
            return False
        now = timezone.now()
        if self.start_date and self.start_date > now:
            return False
        if self.end_date and self.end_date < now:
            return False
        return True


class Notification(models.Model):
    """Admin tomonidan foydalanuvchilarga yuboriladigan bildirishnoma.

    Yaratilishi bilan avtomatik yuborilmaydi -- ``dispatch()`` chaqirilgach
    ``target`` bo'yicha qabul qiluvchilar ro'yxati ``NotificationRecipient``
    sifatida yaratiladi va ``sent_at`` belgilanadi. Shu bilan "qoralama"
    holatida saqlab, keyin yuborish imkoniyati ham qoladi (hozircha
    dashboard formasi darhol yuboradi, lekin model buni cheklamaydi).
    """

    class NotificationType(models.TextChoices):
        INFO = "info", "Ma'lumot"
        PROMO = "promo", "Aksiya"
        UPDATE = "update", "Yangilanish"

    class Target(models.TextChoices):
        ALL = "all", "Barcha foydalanuvchilar"
        ACTIVE = "active", "Faol foydalanuvchilar"
        SELECTED = "selected", "Tanlangan foydalanuvchilar"
        STAFF = "staff", "Xodimlar"

    title = models.CharField("sarlavha", max_length=150)
    message = models.TextField("xabar matni", max_length=2000)
    image = models.ImageField(
        "rasm", upload_to="notifications/%Y/%m/", blank=True, null=True
    )
    notification_type = models.CharField(
        "turi", max_length=10, choices=NotificationType.choices,
        default=NotificationType.INFO,
    )
    link = models.URLField(
        "havola", blank=True,
        help_text="Ixtiyoriy -- bosilganda ochiladigan sahifa.",
    )
    target = models.CharField(
        "qamrov", max_length=10, choices=Target.choices, default=Target.ALL,
    )
    target_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="direct_notifications",
        verbose_name="tanlangan foydalanuvchilar",
        help_text="Faqat qamrov 'Tanlangan foydalanuvchilar' bo'lganda ishlatiladi.",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name="sent_notifications", verbose_name="yuboruvchi",
    )
    created_at = models.DateTimeField("yaratilgan", auto_now_add=True)
    sent_at = models.DateTimeField("yuborilgan", null=True, blank=True, editable=False)

    class Meta:
        verbose_name = "bildirishnoma"
        verbose_name_plural = "bildirishnomalar"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["-created_at"])]

    def __str__(self):
        return self.title

    @property
    def is_sent(self):
        return self.sent_at is not None

    @property
    def recipient_count(self):
        return self.recipients.count()

    @property
    def read_count(self):
        return self.recipients.filter(is_read=True).count()

    @property
    def read_rate(self):
        """O'qilganlar foizi -- yetkazish statistikasi uchun."""
        total = self.recipient_count
        if not total:
            return 0.0
        return round(self.read_count / total * 100, 1)

    def resolve_recipients(self):
        """``target`` maydoniga qarab qabul qiluvchi foydalanuvchilar QuerySet'i."""
        from django.contrib.auth import get_user_model

        User = get_user_model()

        if self.target == self.Target.SELECTED:
            return self.target_users.all()
        if self.target == self.Target.ACTIVE:
            return User.objects.filter(is_active=True)
        if self.target == self.Target.STAFF:
            return User.objects.filter(is_staff=True)
        return User.objects.all()

    def dispatch(self):
        """Qabul qiluvchilarni yaratadi va ``sent_at`` ni belgilaydi.

        Idempotent -- ikkinchi marta chaqirilsa hech narsa qilmaydi (allaqachon
        yuborilgan bildirishnomani qayta yubormaslik uchun).
        """
        if self.is_sent:
            return 0

        recipients = [
            NotificationRecipient(notification=self, user=user)
            for user in self.resolve_recipients()
        ]
        NotificationRecipient.objects.bulk_create(recipients, ignore_conflicts=True)

        from django.utils import timezone

        self.sent_at = timezone.now()
        self.save(update_fields=["sent_at"])
        return len(recipients)


class NotificationRecipient(models.Model):
    """Bitta foydalanuvchiga yetkazilgan bildirishnoma -- o'qilgan/o'qilmagan holati."""

    notification = models.ForeignKey(
        Notification, on_delete=models.CASCADE, related_name="recipients",
        verbose_name="bildirishnoma",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications",
        verbose_name="foydalanuvchi",
    )
    is_read = models.BooleanField("o'qilgan", default=False)
    read_at = models.DateTimeField("o'qilgan vaqti", null=True, blank=True)
    created_at = models.DateTimeField("yetkazilgan", auto_now_add=True)

    class Meta:
        verbose_name = "bildirishnoma qabul qiluvchisi"
        verbose_name_plural = "bildirishnoma qabul qiluvchilari"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["notification", "user"], name="unique_notification_recipient"
            )
        ]
        indexes = [models.Index(fields=["user", "is_read"])]

    def __str__(self):
        return f"{self.notification} -> {self.user}"
