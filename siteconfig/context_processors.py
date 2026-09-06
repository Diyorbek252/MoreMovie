"""Sayt sozlamalarini barcha shablonlarga uzatuvchi kontekst protsessori.

`core.context_processors.site_globals` dan KEYIN ro'yxatga olinadi
(config/settings.py) va undan mustaqil kalit ("site_settings") ishlatadi
-- shu bilan SITE_NAME/SITE_TAGLINE ni bosib qo'ymaydi. Xato yuz bersa
(masalan baza hali tayyor bo'lmasa) butun sayt yiqilib qolmasligi uchun
xavfsiz standart qiymatga qaytadi.
"""

from .models import SiteSettings


def site_settings(request):
    try:
        settings_obj = SiteSettings.load()
    except Exception:
        # Migratsiya hali qo'llanmagan yoki baza vaqtincha mavjud emas --
        # sahifa 500 bo'lib qolmasligi uchun bo'sh ob'ekt bilan davom etamiz.
        settings_obj = SiteSettings()

    return {"site_settings": settings_obj}
