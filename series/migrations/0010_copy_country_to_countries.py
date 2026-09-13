"""Mavjud yagona `country` qiymatini yangi `countries` M2M ga ko'chiradi.

`country` maydonini o'chirishdan OLDIN ishga tushishi kerak — aks holda
mavjud davlat bog'lanishlari yo'qolib qoladi.
"""

from django.db import migrations


def copy_country_forward(apps, schema_editor):
    Series = apps.get_model("series", "Series")
    for series in Series.objects.exclude(country=None):
        series.countries.add(series.country_id)


def copy_country_backward(apps, schema_editor):
    Series = apps.get_model("series", "Series")
    for series in Series.objects.all():
        first_country = series.countries.first()
        if first_country:
            series.country_id = first_country.pk
            series.save(update_fields=["country"])


class Migration(migrations.Migration):

    dependencies = [
        ("series", "0009_series_countries_alter_series_country"),
    ]

    operations = [
        migrations.RunPython(copy_country_forward, copy_country_backward),
    ]
