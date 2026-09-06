"""Bloklangan foydalanuvchini joriy sessiyadan chiqaruvchi middleware."""

from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect


class BlockedUserMiddleware:
    """Admin foydalanuvchini bloklaganda uni darhol tizimdan chiqaradi.

    Backend faqat KIRISH paytida tekshiradi. Agar foydalanuvchi allaqachon
    tizimda bo'lsa va admin uni bloklasa, sessiyasi amal qilishda davom etardi.
    Bu middleware har so'rovda tekshirib, bunday holatni bartaraf qiladi.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)

        if user is not None and user.is_authenticated and user.is_blocked:
            logout(request)
            messages.error(
                request,
                "Hisobingiz administrator tomonidan bloklangan. "
                "Savollaringiz bo'lsa biz bilan bog'laning.",
            )
            return redirect("core:home")

        return self.get_response(request)
