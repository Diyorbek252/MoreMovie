"""Obuna huquqini tekshirish va holatini o'zgartirishning yagona nuqtasi.

Loyihada boshqa hech qanday kod ``Subscription.status``ni to'g'ridan-to'g'ri
tasdiqlash/rad etish yo'nalishida yozmasligi kerak — faqat shu modul orqali,
shunda foydalanuvchiga bildirishnoma yuborish va muddatni hisoblash bir
joyda, izchil bo'lib qoladi.
"""

from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from .models import Subscription


def get_active_subscription(user):
    """Foydalanuvchining hozir amal qilayotgan obunasi, yoki yo'q bo'lsa None.

    Bir so'rov ichida bir necha marta chaqirilganda (masalan context
    processor va view'ning o'zida) qayta so'rov yubormasligi uchun
    `user` obyektining o'zida keshlanadi.
    """
    if not getattr(user, "is_authenticated", False):
        return None

    if not hasattr(user, "_active_subscription_cache"):
        user._active_subscription_cache = (
            Subscription.objects.filter(
                user=user, status=Subscription.Status.ACTIVE, ends_at__gt=timezone.now()
            )
            .select_related("plan")
            .order_by("-ends_at")
            .first()
        )
    return user._active_subscription_cache


def has_premium_access(user):
    """Foydalanuvchi premium filmlarni ko'ra oladimi?"""
    subscription = get_active_subscription(user)
    return bool(subscription and subscription.plan.allows_premium_movies)


def activate_subscription(subscription, admin=None):
    """So'rovni tasdiqlaydi: `PENDING` -> `ACTIVE`, muddatni hisoblaydi.

    Agar foydalanuvchida hali tugamagan boshqa faol obuna bo'lsa, yangi
    muddat o'sha obunaning TUGASH sanasidan boshlanadi — muddatidan oldin
    uzaytirgan foydalanuvchi oldin to'lagan kunlarini yo'qotmaydi.
    """
    now = timezone.now()
    previous = (
        Subscription.objects.filter(
            user=subscription.user, status=Subscription.Status.ACTIVE, ends_at__gt=now
        )
        .exclude(pk=subscription.pk)
        .order_by("-ends_at")
        .first()
    )
    start = previous.ends_at if previous else now

    subscription.status = Subscription.Status.ACTIVE
    subscription.starts_at = start
    subscription.ends_at = start + timedelta(days=subscription.duration_days)
    subscription.reviewed_by = admin
    subscription.reviewed_at = now
    subscription.save(
        update_fields=["status", "starts_at", "ends_at", "reviewed_by", "reviewed_at", "updated_at"]
    )

    _notify_user(
        subscription.user,
        title="Obunangiz faollashtirildi",
        message=f"«{subscription.plan_name}» rejasi faollashtirildi. Amal qilish muddati: {subscription.ends_at:%d.%m.%Y}.",
    )
    return subscription


def reject_subscription(subscription, admin=None, reason=""):
    """So'rovni rad etadi: `PENDING` -> `REJECTED`."""
    subscription.status = Subscription.Status.REJECTED
    subscription.admin_note = reason
    subscription.reviewed_by = admin
    subscription.reviewed_at = timezone.now()
    subscription.save(
        update_fields=["status", "admin_note", "reviewed_by", "reviewed_at", "updated_at"]
    )

    message = f"«{subscription.plan_name}» uchun to'lovingiz tasdiqlanmadi."
    if reason:
        message += f" Sabab: {reason}"
    _notify_user(subscription.user, title="Obuna so'rovi rad etildi", message=message)
    return subscription


def _notify_user(user, title, message):
    """Bitta foydalanuvchiga to'g'ridan-to'g'ri bildirishnoma yuboradi.

    `siteconfig.Notification`ning mavjud fan-out mexanizmidan foydalanadi —
    ``shop.services.notify_admins_new_order`` bilan bir xil naqsh.
    """
    from siteconfig.models import Notification

    notification = Notification.objects.create(
        title=title, message=message, target=Notification.Target.SELECTED,
    )
    notification.target_users.add(user)
    notification.dispatch()
    return notification


def notify_admins_new_subscription(subscription):
    """Yangi obuna so'rovi haqida barcha xodimlarga bildirishnoma yuboradi."""
    from siteconfig.models import Notification

    notification = Notification.objects.create(
        title="Yangi obuna so'rovi",
        message=(
            f"{subscription.user.username} «{subscription.plan_name}» rejasiga "
            f"({subscription.price_paid} so'm) so'rov yubordi."
        ),
        notification_type=Notification.NotificationType.INFO,
        target=Notification.Target.STAFF,
        link=reverse("dashboard:subscription_list"),
    )
    notification.dispatch()
    return notification
