import django.db.models.deletion
from django.db import migrations, models


def copy_person_to_actor(apps, schema_editor):
    """Movies app bilan bir xil naqsh — SeriesCast.person orqali ishtirok
    etgan har bir shaxs uchun (yoki mavjud Actor'ni topib) SeriesCast.actor
    ni to'ldiradi."""
    Actor = apps.get_model("movies", "Actor")
    SeriesCast = apps.get_model("series", "SeriesCast")

    cache = {}
    for cast in SeriesCast.objects.select_related("person").all():
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
        ("series", "0001_initial"),
        ("movies", "0005_split_person_into_director_and_actor"),
    ]

    operations = [
        migrations.AddField(
            model_name="seriescast",
            name="actor",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                related_name="series_roles", to="movies.actor", verbose_name="aktyor",
            ),
        ),
        migrations.RunPython(copy_person_to_actor, noop_reverse),
        migrations.RemoveConstraint(
            model_name="seriescast",
            name="unique_series_person_role",
        ),
        migrations.RemoveField(
            model_name="seriescast",
            name="person",
        ),
        migrations.AlterField(
            model_name="seriescast",
            name="actor",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="series_roles", to="movies.actor", verbose_name="aktyor",
            ),
        ),
        migrations.AddConstraint(
            model_name="seriescast",
            constraint=models.UniqueConstraint(fields=["series", "actor"], name="unique_series_actor_role"),
        ),
        migrations.AlterField(
            model_name="series",
            name="cast",
            field=models.ManyToManyField(
                blank=True, related_name="acted_series", through="series.SeriesCast",
                to="movies.actor", verbose_name="aktyorlar",
            ),
        ),
    ]
