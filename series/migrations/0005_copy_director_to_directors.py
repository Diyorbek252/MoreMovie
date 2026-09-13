"""Mavjud yagona `director` qiymatini yangi `directors` M2M ga ko'chiradi.

`director` maydonini o'chirishdan OLDIN ishga tushishi kerak — aks holda
mavjud rejissyor bog'lanishlari yo'qolib qoladi.
"""

from django.db import migrations


def copy_director_forward(apps, schema_editor):
    Series = apps.get_model("series", "Series")
    for series in Series.objects.exclude(director=None):
        series.directors.add(series.director_id)


def copy_director_backward(apps, schema_editor):
    Series = apps.get_model("series", "Series")
    for series in Series.objects.all():
        first_director = series.directors.first()
        if first_director:
            series.director_id = first_director.pk
            series.save(update_fields=["director"])


class Migration(migrations.Migration):

    dependencies = [
        ("series", "0004_series_directors_alter_series_director"),
    ]

    operations = [
        migrations.RunPython(copy_director_forward, copy_director_backward),
    ]
