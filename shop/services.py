"""Balansni o'zgartirishning yagona nuqtasi.

Loyihada boshqa hech qanday kod ``Profile.balance`` ni to'g'ridan-to'g'ri
yozmasligi kerak — faqat shu modul orqali. Shunda har bir o'zgarish
``CinepointTransaction`` tarixida qoladi va tekshirilishi mumkin.
"""

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import F

from users.models import Profile

from .models import CinepointTransaction


class InsufficientBalanceError(Exception):
    """Debet balansdan oshib ketganda ko'tariladi."""


def adjust_balance(user, amount, reason, note="", related=None, created_by=None):
    """``Profile.balance`` ni atomik o'zgartiradi va tranzaksiya yozadi.

    ``amount`` musbat bo'lsa kredit, manfiy bo'lsa debet. Debet balansdan
    ko'p bo'lsa hech narsa yozilmaydi va ``InsufficientBalanceError``
    ko'tariladi — bu shartli ``UPDATE ... WHERE balance >= X`` orqali
    ``select_for_update()``siz ham xavfsiz (loyiha SQLite'da ishlaydi,
    u qator qulflashni qo'llab-quvvatlamaydi).
    """
    with transaction.atomic():
        if amount < 0:
            rows = Profile.objects.filter(
                user_id=user.pk, balance__gte=-amount
            ).update(balance=F("balance") + amount)
            if not rows:
                raise InsufficientBalanceError("Balans yetarli emas.")
        else:
            Profile.objects.filter(user_id=user.pk).update(balance=F("balance") + amount)

        return CinepointTransaction.objects.create(
            user=user,
            amount=amount,
            reason=reason,
            note=note,
            content_object=related,
            created_by=created_by,
        )


def has_earned(user, reason, related):
    """Shu obyekt uchun (masalan aynan shu film/sharh) mukofot avval
    berilgan-berilmaganini tekshiradi — takroriy mukofotning oldini oladi.
    """
    content_type = ContentType.objects.get_for_model(related)
    return CinepointTransaction.objects.filter(
        user=user, reason=reason, content_type=content_type, object_id=related.pk
    ).exists()
