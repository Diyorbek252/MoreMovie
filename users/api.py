"""AJAX endpointlar — foydalanuvchi sozlamalari.

`movies/api.py` bilan bir xil naqsh: POST + login talab qiladi, CSRF
himoyasi Django middleware tomonidan avtomatik qo'llanadi.
"""

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST


@login_required
@require_POST
def dismiss_continue_watching(request):
    """Bosh sahifadagi «Davom ettirish» bo'limini yashiradi.

    POST /api/continue-watching/dismiss/

    Bitta so'rov — bo'lim shu foydalanuvchi uchun butunlay o'chadi
    (`Profile.show_continue_watching`), keyingi kirishlarida ham
    ko'rinmaydi. Qaytarib yoqish faqat profil sozlamalaridan
    (`users:profile_edit`) mumkin — shu sabab bu yerda "qayta yoqish"
    varianti yo'q, faqat bir tomonlama o'chirish.
    """
    profile = request.user.profile
    if profile.show_continue_watching:
        profile.show_continue_watching = False
        profile.save(update_fields=["show_continue_watching"])

    return JsonResponse(
        {
            "message": (
                "«Davom ettirish» bo'limi yashirildi. Uni profil "
                "sozlamalaridan istalgan payt qaytarib yoqishingiz mumkin."
            ),
        }
    )
