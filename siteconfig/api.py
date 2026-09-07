"""Foydalanuvchining o'ziga yuborilgan bildirishnomalari — public AJAX.

Bu yerdagi endpointlar `movies/api.py` bilan bir xil naqshda: `login_required`
+ `require_POST` (o'qish uchun GET), CSRF himoyasi Django middleware orqali.
Har bir foydalanuvchi FAQAT o'ziga tegishli `NotificationRecipient`
yozuvlarini ko'radi/o'zgartiradi — `get_object_or_404` har doim
`user=request.user` bilan filtrlanadi, shu bilan boshqa foydalanuvchining
bildirishnomasini "o'qilgan" deb belgilab qo'yish imkonsiz.
"""

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import NotificationRecipient

RECENT_LIMIT = 15


def _serialize(recipient):
    notification = recipient.notification
    return {
        "id": recipient.id,
        "title": notification.title,
        "message": notification.message,
        "type": notification.notification_type,
        "link": notification.link,
        "image": notification.image.url if notification.image else "",
        "is_read": recipient.is_read,
        "created_at": recipient.created_at.strftime("%d.%m.%Y %H:%M"),
    }


@login_required
def recent_notifications(request):
    """GET /api/notifications/ — oxirgi bildirishnomalar + o'qilmagan son.

    Dropdown ochilganda va navbar birinchi yuklanganda chaqiriladi.
    """
    recipients = (
        NotificationRecipient.objects.filter(user=request.user)
        .select_related("notification")
        .order_by("-created_at")[:RECENT_LIMIT]
    )
    unread_count = NotificationRecipient.objects.filter(
        user=request.user, is_read=False
    ).count()

    return JsonResponse(
        {
            "results": [_serialize(recipient) for recipient in recipients],
            "unread_count": unread_count,
        }
    )


@login_required
@require_POST
def mark_read(request, pk):
    """POST /api/notifications/<id>/read/ — bitta bildirishnomani o'qilgan qiladi."""
    recipient = get_object_or_404(NotificationRecipient, pk=pk, user=request.user)

    if not recipient.is_read:
        recipient.is_read = True
        recipient.read_at = timezone.now()
        recipient.save(update_fields=["is_read", "read_at"])

    return JsonResponse(
        {
            "marked": True,
            "unread_count": NotificationRecipient.objects.filter(
                user=request.user, is_read=False
            ).count(),
        }
    )


@login_required
@require_POST
def mark_all_read(request):
    """POST /api/notifications/read-all/ — barchasini o'qilgan deb belgilaydi."""
    NotificationRecipient.objects.filter(user=request.user, is_read=False).update(
        is_read=True, read_at=timezone.now()
    )
    return JsonResponse({"marked": True, "unread_count": 0})
