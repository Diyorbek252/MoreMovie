"""Bosh sahifa bo'limlarini hozirgi (qattiq kodlangan) tartibda yaratadi.

Ishlatish:
    python manage.py seed_homepage_sections

Bu komanda `core/views.py` dagi `HomeView._get_shared_sections()` da
hozir qattiq kodlangan bo'limlarni AYNAN o'sha tartib va sarlavhalar
bilan bazaga ko'chiradi -- shuning uchun ishga tushirilgandan keyin ham
bosh sahifada VIZUAL O'ZGARISH BO'LMAYDI. Faqat shundan keyin admin
panelidan bo'limlarni yoqib/o'chirish va tartiblash imkoniyati ochiladi.

Idempotent -- qayta ishga tushirish xavfsiz (mavjud kalitlar
yangilanadi, yo'qlari yaratiladi).
"""

from django.core.management.base import BaseCommand

from siteconfig.models import HomepageSection

# (key, title, order, item_limit) -- core/views.py dagi hozirgi tartib bilan bir xil.
SECTIONS = [
    (HomepageSection.Key.HERO, "Bugungi tanlov", 0, 1),
    (HomepageSection.Key.CONTINUE, "Davom ettirish", 10, 12),
    (HomepageSection.Key.TRENDING, "Trending", 20, 14),
    (HomepageSection.Key.POPULAR, "Popular Movies", 30, 14),
    (HomepageSection.Key.NEW_RELEASES, "New Releases", 40, 14),
    (HomepageSection.Key.TOP_RATED, "Top Rated", 50, 14),
    (HomepageSection.Key.GENRES, "Janrlar", 60, 10),
    (HomepageSection.Key.FEATURED, "Featured", 70, 14),
]


class Command(BaseCommand):
    help = "Bosh sahifa bo'limlarini hozirgi tartibda HomepageSection jadvaliga yozadi."

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        for key, title, order, item_limit in SECTIONS:
            section, created = HomepageSection.objects.update_or_create(
                key=key,
                defaults={
                    "title": title,
                    "order": order,
                    "item_limit": item_limit,
                    "is_active": True,
                },
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"  + {title} ({key})"))
            else:
                updated_count += 1
                self.stdout.write(f"  = {title} ({key}) -- yangilandi")

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Tayyor. {created_count} ta yaratildi, {updated_count} ta yangilandi."
            )
        )
