"""Sayt darajasidagi modellar."""

from django.db import models


class ContactMessage(models.Model):
    """Contact sahifasidan yuborilgan xabar.

    Xabarlar bazaga yoziladi va dashboard'da ko'riladi — bu SMTP sozlanmagan
    development muhitida ham murojaatlar yo'qolmasligini ta'minlaydi.
    """

    name = models.CharField("ism", max_length=120)
    email = models.EmailField("email")
    subject = models.CharField("mavzu", max_length=200)
    message = models.TextField("xabar", max_length=3000)
    is_read = models.BooleanField("o'qilgan", default=False)
    created_at = models.DateTimeField("yuborilgan", auto_now_add=True)

    class Meta:
        verbose_name = "murojaat"
        verbose_name_plural = "murojaatlar"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["is_read", "-created_at"])]

    def __str__(self):
        return f"{self.name}: {self.subject}"
