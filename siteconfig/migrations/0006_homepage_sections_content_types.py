"""Bosh sahifa bo'limlarini yangi tuzilishga o'tkazadi.

Eski bo'limlar (Trending, Popular, New Releases, Top Rated, Featured)
o'rniga kontent turi bo'yicha to'rtta bo'lim keladi: Premyeralar,
Kinolar, Multfilmlar, Seriallar. «Hero», «Davom ettirish» va «Janrlar»
o'z joyida qoladi.

Eski yozuvlar faqat konfiguratsiya bo'lgani uchun (kontent emas)
ularni o'chirish xavfsiz -- orqaga qaytarilganda seed komandasi
ularni qayta yaratadi.
"""

from django.db import migrations

# (key, title, order, item_limit)
NEW_SECTIONS = [
    ("premieres", "Premyeralar", 20, 14),
    ("movies", "Kinolar", 30, 14),
    ("cartoons", "Multfilmlar", 40, 14),
    ("series", "Seriallar", 50, 14),
]

OBSOLETE_KEYS = ["trending", "popular", "new_releases", "top_rated", "featured"]


def forwards(apps, schema_editor):
    HomepageSection = apps.get_model("siteconfig", "HomepageSection")

    # Jadval umuman bo'sh bo'lsa -- admin `seed_homepage_sections` ni hali
    # ishga tushirmagan. Bunday holatda bo'limlar standart holatda
    # ko'rsatiladi (core.views.HomeView), shuning uchun yozuv yaratmaymiz.
    if not HomepageSection.objects.exists():
        return

    # Yangi bo'limlar eskilarining o'rnini egallaydi -- tartibni saqlab
    # qolish uchun o'chirishdan oldin yaratamiz.
    for key, title, order, item_limit in NEW_SECTIONS:
        HomepageSection.objects.get_or_create(
            key=key,
            defaults={
                "title": title,
                "order": order,
                "item_limit": item_limit,
                "is_active": True,
            },
        )

    HomepageSection.objects.filter(key__in=OBSOLETE_KEYS).delete()


def backwards(apps, schema_editor):
    HomepageSection = apps.get_model("siteconfig", "HomepageSection")
    HomepageSection.objects.filter(key__in=[key for key, *_ in NEW_SECTIONS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("siteconfig", "0005_alter_homepagesection_key"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
