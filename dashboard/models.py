"""Dashboard o'z domen modeliga ega emas — u boshqa ilovalarning
modellarini boshqaradi. Bu yerdagi ikkita model istisno:

- `DashboardAccess` — jadval yaratmaydi (``managed = False``), faqat
  standart CRUD ruxsatlaridan tashqari maxsus ruxsatlarni (masalan
  "boshqaruv paneliga kirish") saqlash uchun "ilgak" vazifasini bajaradi.
- `ActivityLog` — kim, qachon, nima qildi — audit uchun.
"""

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class DashboardAccess(models.Model):
    """Haqiqiy jadvalsiz model — faqat maxsus ruxsatlarni e'lon qilish uchun.

    ``managed = False`` bo'lgani uchun migratsiya jadval yaratmaydi, lekin
    ``permissions`` ro'yxatidagi har bir yozuv uchun Django ``post_migrate``
    signali orqali ``Permission`` qatorini avtomatik yaratadi — ular
    ``user.has_perm("dashboard.access_dashboard")`` kabi tekshiriladi.
    """

    class Meta:
        managed = False
        default_permissions = ()
        permissions = [
            ("access_dashboard", "Boshqaruv paneliga kirish"),
            ("view_analytics", "Analitikani ko'rish"),
            ("manage_settings", "Sayt sozlamalarini boshqarish"),
            ("manage_banners", "Bannerlarni boshqarish"),
            ("send_notifications", "Bildirishnoma yuborish"),
            ("manage_roles", "Rollarni boshqarish"),
            ("manage_homepage", "Bosh sahifa bo'limlarini boshqarish"),
        ]


class ActivityLog(models.Model):
    """Admin panelidagi muhim harakatlar tarixi (audit log)."""

    class Action(models.TextChoices):
        CREATE = "create", "Yaratildi"
        UPDATE = "update", "Yangilandi"
        DELETE = "delete", "O'chirildi"
        PUBLISH = "publish", "Chop etildi/yashirildi"
        MODERATE = "moderate", "Moderatsiya qilindi"
        SEND = "send", "Yuborildi"
        SETTINGS = "settings", "Sozlamalar o'zgartirildi"

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="dashboard_actions",
        verbose_name="bajaruvchi",
    )
    action = models.CharField("harakat", max_length=20, choices=Action.choices)

    # Generic FK — istalgan model obyektiga ishora qilish uchun (Movie, Series,
    # User va h.k.), shu bilan har bir model uchun alohida log jadval kerak emas.
    content_type = models.ForeignKey(
        ContentType, on_delete=models.SET_NULL, null=True, blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")

    target_repr = models.CharField(
        "nishon tavsifi", max_length=200, blank=True,
        help_text="Obyekt o'chirilgandan keyin ham o'qilishi uchun matn ko'rinishida saqlanadi.",
    )
    note = models.CharField("izoh", max_length=255, blank=True)
    created_at = models.DateTimeField("vaqti", auto_now_add=True)

    class Meta:
        verbose_name = "faoliyat yozuvi"
        verbose_name_plural = "faoliyat yozuvlari"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["-created_at"])]

    def __str__(self):
        actor_name = self.actor.username if self.actor else "tizim"
        return f"{actor_name}: {self.get_action_display()} — {self.target_repr}"
