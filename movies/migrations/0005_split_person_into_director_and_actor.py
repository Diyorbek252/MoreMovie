import django.db.models.deletion
from django.db import migrations, models


def copy_person_to_actor(apps, schema_editor):
    """MovieCast.person (endi Director) orqali ishtirok etgan har bir shaxs
    uchun mos Actor yozuvini yaratadi va MovieCast.actor ni shunga bog'laydi.

    Bitta odam bir nechta filmda aktyor bo'lgan bo'lishi mumkin — shuning
    uchun full_name bo'yicha keshlaymiz, bir xil ism uchun bitta Actor.
    """
    Director = apps.get_model("movies", "Director")
    Actor = apps.get_model("movies", "Actor")
    MovieCast = apps.get_model("movies", "MovieCast")

    cache = {}
    for cast in MovieCast.objects.select_related("person").all():
        full_name = cast.person.full_name
        if full_name not in cache:
            actor, created = Actor.objects.get_or_create(full_name=full_name)
            if created:
                actor.slug = _unique_slug(Actor, full_name)
                actor.photo = cast.person.photo
                actor.bio = cast.person.bio
                actor.save()
            cache[full_name] = actor
        cast.actor = cache[full_name]
        cast.save(update_fields=["actor"])


def _unique_slug(model, value):
    from django.utils.text import slugify

    base = slugify(value, allow_unicode=False) or "element"
    slug = base
    counter = 2
    while model.objects.filter(slug=slug).exists():
        slug = f"{base}-{counter}"
        counter += 1
    return slug


def noop_reverse(apps, schema_editor):
    """Teskari yo'nalishda hech narsa qilinmaydi — Actor yozuvlari qoladi."""


class Migration(migrations.Migration):

    dependencies = [
        ("movies", "0004_alter_movie_download_url"),
        ("series", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Actor",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="yaratilgan")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="yangilangan")),
                ("full_name", models.CharField(max_length=150, verbose_name="to'liq ism")),
                ("slug", models.SlugField(blank=True, max_length=160, unique=True, verbose_name="slug")),
                ("photo", models.ImageField(blank=True, null=True, upload_to="actors/", verbose_name="surat")),
                ("bio", models.TextField(blank=True, verbose_name="qisqacha")),
            ],
            options={
                "verbose_name": "aktyor",
                "verbose_name_plural": "aktyorlar",
                "ordering": ["full_name"],
            },
        ),
        migrations.AddIndex(
            model_name="actor",
            index=models.Index(fields=["full_name"], name="movies_acto_full_na_a580fe_idx"),
        ),
        migrations.RenameModel(old_name="Person", new_name="Director"),
        migrations.AlterModelOptions(
            name="director",
            options={
                "verbose_name": "rejissyor",
                "verbose_name_plural": "rejissyorlar",
                "ordering": ["full_name"],
            },
        ),
        migrations.AlterField(
            model_name="director",
            name="photo",
            field=models.ImageField(blank=True, null=True, upload_to="directors/", verbose_name="surat"),
        ),
        migrations.AddField(
            model_name="moviecast",
            name="actor",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                related_name="roles", to="movies.actor", verbose_name="aktyor",
            ),
        ),
        migrations.RunPython(copy_person_to_actor, noop_reverse),
        migrations.RemoveConstraint(
            model_name="moviecast",
            name="unique_movie_person_role",
        ),
        migrations.RemoveField(
            model_name="moviecast",
            name="person",
        ),
        migrations.AlterField(
            model_name="moviecast",
            name="actor",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="roles", to="movies.actor", verbose_name="aktyor",
            ),
        ),
        migrations.AddConstraint(
            model_name="moviecast",
            constraint=models.UniqueConstraint(fields=["movie", "actor"], name="unique_movie_actor_role"),
        ),
        migrations.AlterField(
            model_name="movie",
            name="cast",
            field=models.ManyToManyField(
                blank=True, related_name="acted_movies", through="movies.MovieCast",
                to="movies.actor", verbose_name="aktyorlar",
            ),
        ),
    ]
