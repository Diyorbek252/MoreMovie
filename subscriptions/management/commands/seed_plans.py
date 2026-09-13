"""Boshlang'ich obuna rejalarini yaratadi (Standart / Premium).

Ishlatish:
    python manage.py seed_plans
    python manage.py seed_plans --reset   # avval mavjud rejalarni o'chiradi

Idempotent: qayta ishga tushirilsa mavjud rejalarni (slug bo'yicha)
yangilaydi, takror yaratmaydi.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from subscriptions.models import Plan, PlanPrice

PLANS = [
    {
        "name": "Standart",
        "tagline": "Reklamasiz tomosha",
        "description": "Barcha ochiq filmlarni reklamasiz tomosha qiling.",
        "features": "Reklamasiz tomosha\nProfilda nishon",
        "level": 1,
        "allows_premium_movies": False,
        "has_badge": True,
        "is_ad_free": True,
        "is_highlighted": False,
        "order": 1,
        "prices": [
            {"label": "1 oy", "duration_days": 30, "price": 15000, "order": 1},
            {"label": "3 oy", "duration_days": 90, "price": 40000, "old_price": 45000, "order": 2},
            {"label": "1 yil", "duration_days": 365, "price": 140000, "old_price": 180000, "order": 3},
        ],
    },
    {
        "name": "Premium",
        "tagline": "Eng ommabop tanlov",
        "description": "Premium filmlar, reklamasiz tomosha va oltin nishon.",
        "features": "Premium filmlarni ko'rish\nReklamasiz tomosha\nProfilda oltin nishon",
        "level": 2,
        "allows_premium_movies": True,
        "has_badge": True,
        "is_ad_free": True,
        "is_highlighted": True,
        "order": 2,
        "prices": [
            {"label": "1 oy", "duration_days": 30, "price": 30000, "order": 1},
            {"label": "3 oy", "duration_days": 90, "price": 80000, "old_price": 90000, "order": 2},
            {"label": "1 yil", "duration_days": 365, "price": 280000, "old_price": 360000, "order": 3},
        ],
    },
]


class Command(BaseCommand):
    help = "Boshlang'ich obuna rejalarini (Standart / Premium) yaratadi."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset", action="store_true",
            help="Avval mavjud barcha rejalarni o'chiradi, keyin qaytadan yaratadi.",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            count = Plan.objects.count()
            Plan.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"{count} ta mavjud reja o'chirildi."))

        with transaction.atomic():
            for plan_data in PLANS:
                prices = plan_data["prices"]
                defaults = {key: value for key, value in plan_data.items() if key != "prices"}
                plan, created = Plan.objects.update_or_create(
                    name=plan_data["name"], defaults=defaults
                )

                for price_data in prices:
                    PlanPrice.objects.update_or_create(
                        plan=plan, label=price_data["label"], defaults=price_data
                    )

                verb = "yaratildi" if created else "yangilandi"
                self.stdout.write(
                    self.style.SUCCESS(f"«{plan.name}» rejasi {verb} — {len(prices)} ta narx.")
                )
