"""Autentifikatsiya backend'i — username yoki email bilan kirish."""

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

User = get_user_model()


class EmailOrUsernameBackend(ModelBackend):
    """Foydalanuvchi login maydoniga username YOKI email kiritishi mumkin.

    Xavfsizlik eslatmalari:
    - Foydalanuvchi topilmasa ham parol hash'lash bajariladi (User().set_password
      emas, balki run_password_hasher) — bu "timing attack" orqali qaysi email
      ro'yxatdan o'tganini aniqlashga yo'l qo'ymaydi.
    - Bloklangan foydalanuvchi user_can_authenticate() da rad etiladi.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        # Django ba'zi joylarda USERNAME_FIELD nomi bilan uzatadi.
        login_value = username or kwargs.get(User.USERNAME_FIELD) or kwargs.get("email")

        if login_value is None or password is None:
            return None

        try:
            # iexact — katta/kichik harf farq qilmaydi.
            user = User.objects.get(
                Q(username__iexact=login_value) | Q(email__iexact=login_value)
            )
        except User.DoesNotExist:
            # Vaqt farqini yo'qotish uchun baribir hash hisoblaymiz.
            User().set_password(password)
            return None
        except User.MultipleObjectsReturned:
            # Nazariy jihatdan bo'lmasligi kerak (ikkalasi ham unique),
            # lekin bo'lsa — username bo'yicha mos kelganini olamiz.
            user = (
                User.objects.filter(username__iexact=login_value).first()
                or User.objects.filter(email__iexact=login_value).first()
            )
            if user is None:
                return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    def user_can_authenticate(self, user):
        """Faol va bloklanmagan foydalanuvchilargina kira oladi."""
        return super().user_can_authenticate(user) and not user.is_blocked
