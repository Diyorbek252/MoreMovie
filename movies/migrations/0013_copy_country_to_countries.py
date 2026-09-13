"""Mavjud yagona `country` qiymatini yangi `countries` M2M ga ko'chiradi.

`country` maydonini o'chirishdan OLDIN ishga tushishi kerak — aks holda
mavjud davlat bog'lanishlari yo'qolib qoladi.
"""

from django.db import migrations


def copy_country_forward(apps, schema_editor):
    Movie = apps.get_model("movies", "Movie")
    for movie in Movie.objects.exclude(country=None):
        movie.countries.add(movie.country_id)


def copy_country_backward(apps, schema_editor):
    Movie = apps.get_model("movies", "Movie")
    for movie in Movie.objects.all():
        first_country = movie.countries.first()
        if first_country:
            movie.country_id = first_country.pk
            movie.save(update_fields=["country"])


class Migration(migrations.Migration):

    dependencies = [
        ("movies", "0012_movie_countries_alter_movie_country"),
    ]

    operations = [
        migrations.RunPython(copy_country_forward, copy_country_backward),
    ]
