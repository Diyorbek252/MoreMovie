"""Boshqaruv paneli uchun ruxsat tekshiruvi.

``DashboardPermissionMixin`` — barcha class-based view'lar uchun.
``dashboard_perm_required`` — AJAX funksiya-view'lar uchun bir xil
JSON xato formatini beruvchi dekorator (``static/js/main.js`` dagi
``MM.postJSON`` xato xabarini ``payload.error`` dan o'qiydi).

``StaffRequiredMixin`` eski nom bilan saqlanadi (subclass-alias) —
mavjud 11 ta view shu nomni import qilib ishlatadi va ular
o'zgarishsiz ishlayveradi; ruxsatlarni birma-bir kiritish uchun ularga
keyinroq ``required_perms`` qo'shiladi.
"""

import functools

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse

from .navigation import build_nav, get_nav_counts


class DashboardPermissionMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Sahifaga kirish uchun: xodim, bloklanmagan va kerakli ruxsatlarga ega.

    ``required_perms`` — bo'sh bo'lsa faqat panelga umumiy kirish
    (``dashboard.access_dashboard``) tekshiriladi. To'ldirilsa, shu
    ruxsatlar ham talab qilinadi (``require_all_perms=True`` bo'lsa
    hammasi, ``False`` bo'lsa kamida bittasi kifoya).

    Superuser har doim o'tadi — ruxsatlar hali tayinlanmagan bo'lsa ham
    (masalan ``seed_roles`` hali ishga tushirilmagan yangi muhitda)
    admin panelidan chetlab qolmasligi uchun.
    """

    raise_exception = True
    required_perms: list[str] = []
    require_all_perms: bool = True

    def test_func(self):
        user = self.request.user

        if not (user.is_authenticated and user.is_staff and not user.is_blocked):
            return False

        if user.is_superuser:
            return True

        if not user.has_perm("dashboard.access_dashboard"):
            return False

        if not self.required_perms:
            return True

        checker = all if self.require_all_perms else any
        return checker(user.has_perm(perm) for perm in self.required_perms)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["nav_counts"] = get_nav_counts()
        context["dash_nav"] = build_nav(self.request)
        return context


# Orqaga moslik: mavjud view'lar shu nomni import qiladi. Ruxsatlar hali
# ular ustiga qo'shilmagan bo'lsa ham (required_perms bo'sh), ular avval
# ishlagani kabi — faqat is_staff tekshiruvi bilan — ishlayveradi.
class StaffRequiredMixin(DashboardPermissionMixin):
    pass


def dashboard_perm_required(*perms, require_all=True):
    """AJAX funksiya-view'lar uchun ruxsat dekoratori.

    Muvaffaqiyatsiz bo'lsa ``_staff_check`` bilan bir xil JSON javobni
    qaytaradi — ``{"error": "Ruxsat yo'q"}``, status 403 — shunda
    ``MM.postJSON`` xato xabarini to'g'ri ko'rsatadi.
    """

    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = request.user

            if not (user.is_authenticated and user.is_staff and not user.is_blocked):
                return JsonResponse({"error": "Ruxsat yo'q"}, status=403)

            if not user.is_superuser:
                if not user.has_perm("dashboard.access_dashboard"):
                    return JsonResponse({"error": "Ruxsat yo'q"}, status=403)
                if perms:
                    checker = all if require_all else any
                    if not checker(user.has_perm(p) for p in perms):
                        return JsonResponse({"error": "Ruxsat yo'q"}, status=403)

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
