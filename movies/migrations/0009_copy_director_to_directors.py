"""Mavjud yagona `director` qiymatini yangi `directors` M2M ga ko'chiradi.

`director` maydonini o'chirishdan OLDIN ishga tushishi kerak — aks holda
mavjud rejissyor bog'lanishlari yo'qolib qoladi.
"""

from django.db import migrations


def copy_director_forward(apps, schema_editor):
    Movie = apps.get_model("movies", "Movie")
    for movie in Movie.objects.exclude(director=None):
        movie.directors.add(movie.director_id)


def copy_director_backward(apps, schema_editor):
    Movie = apps.get_model("movies", "Movie")
    for movie in Movie.objects.all():
        first_director = movie.directors.first()
        if first_director:
            movie.director_id = first_director.pk
            movie.save(update_fields=["director"])


class Migration(migrations.Migration):

    dependencies = [
        ("movies", "0008_movie_directors_alter_movie_director"),
    ]

    operations = [
        migrations.RunPython(copy_director_forward, copy_director_backward),
    ]
