"""«Janrlar» bo'limini yangi bo'limlardan keyinga tushiradi.

0006 da eski bo'limlar (Trending, Popular, ...) o'chirilib, o'rniga
Premyeralar / Kinolar / Multfilmlar / Seriallar keldi. «Janrlar» ning
tartib raqami esa eski qo'shnilariga nisbatan qo'yilgan edi -- yangi
bo'limlar 20..50 oralig'ida bo'lgani uchun u to'satdan eng tepaga
chiqib qolishi mumkin. Bu yerda uni ro'yxatning oxiriga qaytaramiz.

Faqat tartibga tegadi -- bo'limning yoqilgan/o'chirilgan holati va
sarlavhasi admin qo'ygan holicha qoladi.
"""

from django.db import migrations

CONTENT_KEYS = ["premieres", "movies", "cartoons", "series"]


def forwards(apps, schema_editor):
    HomepageSection = apps.get_model("siteconfig", "HomepageSection")

    genres = HomepageSection.objects.filter(key="genres").first()
    if genres is None:
        return

    content = HomepageSection.objects.filter(key__in=CONTENT_KEYS)
    if not content.exists():
        return

    last = max(row.order for row in content)
    if genres.order < last:
        genres.order = last + 10
        genres.save(update_fields=["order"])


def backwards(apps, schema_editor):
    # Tartib -- admin istalgan vaqtda o'zgartira oladigan sozlama;
    # orqaga qaytarishda tegmaymiz.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("siteconfig", "0006_homepage_sections_content_types"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
