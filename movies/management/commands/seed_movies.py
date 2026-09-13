"""Test ma'lumotlarini yaratuvchi management komandasi.

Ishlatish:
    python manage.py seed_movies
    python manage.py seed_movies --reset   # avval mavjud filmlarni o'chiradi

HUQUQIY ESLATMA
---------------
Bu yerdagi barcha filmlar — Blender Foundation ning ochiq (open movie)
loyihalari. Ular Creative Commons Attribution litsenziyasi ostida erkin
tarqatiladi, shuning uchun ularni namoyish qilish va yuklab olish qonuniy.
Hech qanday pirat yoki mualliflik huquqi bilan himoyalangan kontent yo'q.

Posterlar dasturiy ravishda (Pillow bilan) yaratiladi — tashqi rasm
yuklab olinmaydi, shuning uchun komanda internetsiz ham ishlaydi.
"""

import io
import random

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction

from movies.models import (
    Actor,
    Country,
    Director,
    Genre,
    Language,
    Movie,
    MovieCast,
)

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover
    Image = None


# ---------------------------------------------------------------------------
# Ma'lumotnomalar
# ---------------------------------------------------------------------------

GENRES = [
    ("Action", "action", 1),
    ("Adventure", "adventure", 2),
    ("Animation", "animation", 3),
    ("Comedy", "comedy", 4),
    ("Drama", "drama", 5),
    ("Fantasy", "fantasy", 6),
    ("Sci-Fi", "scifi", 7),
    ("Thriller", "thriller", 8),
    ("Documentary", "documentary", 9),
    ("Family", "family", 10),
]

COUNTRIES = [
    ("Netherlands", "NLD"),
    ("United States", "USA"),
    ("France", "FRA"),
    ("Germany", "DEU"),
    ("Uzbekistan", "UZB"),
]

LANGUAGES = [
    ("English", "en"),
    ("Uzbek", "uz"),
    ("Russian", "ru"),
    ("French", "fr"),
    ("No dialogue", "zxx"),
]

PEOPLE = [
    "Sacha Goedegebure", "Ton Roosendaal", "Colin Levy", "Ian Hubert",
    "Mathieu Auvray", "Hjalti Hjalmarsson", "Beorn Leonard", "Francesco Siddi",
    "Andy Goralczyk", "Pablo Vazquez", "Angela Guenette", "Nathan Vegdahl",
    "Sarah Laufer", "David Revoy", "Manu Jarvinen",
]

# Blender Foundation ochiq filmlari — barchasi CC BY litsenziyasi ostida.
BLENDER_HOST = "https://download.blender.org/peach/bigbuckbunny_movies"

MOVIES = [
    {
        "title": "Big Buck Bunny",
        "year": 2008,
        "duration": 10,
        "genres": ["Animation", "Comedy", "Family"],
        "director": "Sacha Goedegebure",
        "cast": ["Angela Guenette", "Nathan Vegdahl", "Beorn Leonard"],
        "language": "No dialogue",
        "country": "Netherlands",
        "quality": "FHD",
        "imdb": 6.4,
        "license_note": "CC BY 3.0 — Blender Foundation",
        "video": f"{BLENDER_HOST}/big_buck_bunny_480p_h264.mov",
        "trailer": "https://www.youtube.com/embed/YE7VzlLtp-4",
        "featured": True,
        "colors": ("#1b5e20", "#8bc34a"),
        "description": (
            "Katta va yumshoq ko'ngilli quyon Big Buck Bunny tinch o'rmonda "
            "yashaydi. Ammo uchta qo'pol kemiruvchi uning osoyishtaligini buzib, "
            "atrofdagi mayda jonivorlarni xafa qila boshlaydi. Sabr kosasi to'lgan "
            "quyon o'ziga xos, aql bilan o'ylangan javob tayyorlaydi. Blender "
            "Foundation ning birinchi keng tarqalgan ochiq animatsion filmi."
        ),
    },
    {
        "title": "Sintel",
        "year": 2010,
        "duration": 15,
        "genres": ["Animation", "Fantasy", "Adventure"],
        "director": "Colin Levy",
        "cast": ["Halina Reijn", "Thom Hoffman"],
        "language": "English",
        "country": "Netherlands",
        "quality": "FHD",
        "imdb": 7.4,
        "license_note": "CC BY 3.0 — Blender Foundation",
        "video": "https://download.blender.org/durian/trailer/sintel_trailer-480p.mp4",
        "trailer": "https://www.youtube.com/embed/eRsGyueVLvQ",
        "featured": True,
        "colors": ("#37474f", "#ff7043"),
        "description": (
            "Yolg'iz sayohatchi qiz Sintel yo'qolgan ajdaho bolasi Skoni izlab, "
            "xavfli o'lkalarni kezib chiqadi. Uzoq yillik qidiruv uni o'zi "
            "kutmagan, achchiq haqiqat sari yetaklaydi. Durian loyihasi doirasida "
            "yaratilgan, kuchli hissiy ta'sirga ega qisqa metrajli fantaziya."
        ),
    },
    {
        "title": "Tears of Steel",
        "year": 2012,
        "duration": 12,
        "genres": ["Sci-Fi", "Action", "Drama"],
        "director": "Ian Hubert",
        "cast": ["Derek de Lint", "Sergio Hasselbaink", "Rogier Schippers"],
        "language": "English",
        "country": "Netherlands",
        "quality": "FHD",
        "imdb": 6.6,
        "license_note": "CC BY 3.0 — Blender Foundation",
        "video": "https://download.blender.org/mango/tearsofsteel_4k.mov",
        "trailer": "https://www.youtube.com/embed/R6MlUcmOul8",
        "featured": True,
        "colors": ("#263238", "#00bcd4"),
        "description": (
            "Kelajakdagi Amsterdamda bir guruh olimlar dunyoni robotlar "
            "hujumidan qutqarishga urinadi. Yechim esa o'tmishdagi bir "
            "munosabatni tiklashdan o'tadi. Mango loyihasi — Blender ning "
            "jonli suratga olish va VFX ni birlashtirgan ochiq filmi."
        ),
    },
    {
        "title": "Elephants Dream",
        "year": 2006,
        "duration": 11,
        "genres": ["Animation", "Sci-Fi", "Drama"],
        "director": "Ton Roosendaal",
        "cast": ["Tygo Gernandt", "Cas Jansen"],
        "language": "English",
        "country": "Netherlands",
        "quality": "HD",
        "imdb": 6.8,
        "license_note": "CC BY 2.5 — Blender Foundation",
        "video": "https://archive.org/download/ElephantsDream/ed_hd.mp4",
        "trailer": "https://www.youtube.com/embed/TLkA0RELQ1g",
        "featured": False,
        "colors": ("#4a148c", "#ce93d8"),
        "description": (
            "Emo va Proog ulkan, doimo o'zgarib turuvchi mexanik dunyoda "
            "sayohat qiladilar. Ikkisi bu joyni butunlay boshqacha ko'radi — "
            "va bu tafovut ular orasidagi ziddiyatni kuchaytiradi. Dunyodagi "
            "birinchi ochiq manbali animatsion film."
        ),
    },
    {
        "title": "Spring",
        "year": 2019,
        "duration": 8,
        "genres": ["Animation", "Fantasy", "Family"],
        "director": "Andy Goralczyk",
        "cast": ["Hjalti Hjalmarsson"],
        "language": "No dialogue",
        "country": "Netherlands",
        "quality": "4K",
        "imdb": 7.6,
        "license_note": "CC BY 4.0 — Blender Foundation",
        "video": "https://upload.wikimedia.org/wikipedia/commons/2/22/Spring_-_Blender_Open_Movie.webm",
        "trailer": "https://www.youtube.com/embed/WhWc3b3KhnY",
        "featured": True,
        "colors": ("#1b5e20", "#a5d6a7"),
        "description": (
            "Cho'pon qiz va uning sodiq iti har yili tabiatning uyg'onishini "
            "kuzatib turadi. Qadimiy marosim yana takrorlanar ekan, ular "
            "hayotning aylanma yo'lini yangidan kashf etadi. Nafis chizilgan, "
            "so'zsiz hikoya."
        ),
    },
    {
        "title": "Cosmos Laundromat",
        "year": 2015,
        "duration": 12,
        "genres": ["Animation", "Comedy", "Fantasy"],
        "director": "Mathieu Auvray",
        "cast": ["Pierre Bokma", "Reinout Scholten van Aschat"],
        "language": "English",
        "country": "Netherlands",
        "quality": "FHD",
        "imdb": 7.0,
        "license_note": "CC BY 4.0 — Blender Foundation",
        "video": "https://upload.wikimedia.org/wikipedia/commons/8/87/Cosmos_Laundromat_-_First_Cycle_%282015%29.webm",
        "trailer": "https://www.youtube.com/embed/Y-rmzh0PI3c",
        "featured": False,
        "colors": ("#0d47a1", "#4fc3f7"),
        "description": (
            "Umidsiz qo'y Franck hayotdan voz kechmoqchi bo'lganida sirli sotuvchi "
            "unga cheksiz imkoniyatlar taklif qiladi. Har bir tanlov uni yangi "
            "olamga olib o'tadi. Gooseberry loyihasining birinchi qismi."
        ),
    },
    {
        "title": "Agent 327: Operation Barbershop",
        "year": 2017,
        "duration": 4,
        "genres": ["Animation", "Action", "Comedy"],
        "director": "Hjalti Hjalmarsson",
        "cast": ["Hjalti Hjalmarsson", "Beorn Leonard"],
        "language": "English",
        "country": "Netherlands",
        "quality": "FHD",
        "imdb": 7.2,
        "license_note": "CC BY 4.0 — Blender Foundation",
        "video": "https://upload.wikimedia.org/wikipedia/commons/0/0a/Agent_327_-_Operation_Barbershop.webm",
        "trailer": "https://www.youtube.com/embed/mN0zPOpADL4",
        "featured": False,
        "colors": ("#b71c1c", "#ff8a65"),
        "description": (
            "Gollandiyalik maxfiy agent 327 oddiy sartaroshxonaga kiradi — "
            "lekin u yerda uni tuzoq kutmoqda. Qisqa, tez sur'atli va hazil "
            "bilan to'la jangovar epizod."
        ),
    },
    {
        "title": "Caminandes: Llamigos",
        "year": 2016,
        "duration": 3,
        "genres": ["Animation", "Comedy", "Family"],
        "director": "Pablo Vazquez",
        "cast": ["Pablo Vazquez"],
        "language": "No dialogue",
        "country": "Netherlands",
        "quality": "FHD",
        "imdb": 7.5,
        "license_note": "CC BY 4.0 — Blender Foundation",
        "video": "https://upload.wikimedia.org/wikipedia/commons/1/1c/Caminandes_-_Llamigos.webm",
        "trailer": "https://www.youtube.com/embed/SkVqJ1SGeL0",
        "featured": False,
        "colors": ("#e65100", "#ffcc80"),
        "description": (
            "Lama Koro va pingvin Oti qish o'rtasida qolgan yagona o't uchun "
            "kurashadi. Ikkalasi ham taslim bo'lishni istamaydi. Caminandes "
            "seriyasining eng kulgili qismi."
        ),
    },
    {
        "title": "Glass Half",
        "year": 2015,
        "duration": 3,
        "genres": ["Animation", "Comedy", "Drama"],
        "director": "Beorn Leonard",
        "cast": ["Manu Jarvinen"],
        "language": "English",
        "country": "Netherlands",
        "quality": "HD",
        "imdb": 6.5,
        "license_note": "CC BY 4.0 — Blender Foundation",
        "video": "",
        "trailer": "https://www.youtube.com/embed/-Nl4bcMHqiM",
        "featured": False,
        "colors": ("#004d40", "#80cbc4"),
        "description": (
            "Ikki san'atshunos muzeydagi bir asar haqida bahslashadi. Bahs "
            "tobora qizib boradi va kutilmagan yakun bilan tugaydi. Blender "
            "Institute ning qisqa mashqi."
        ),
    },
    {
        "title": "Hero",
        "year": 2018,
        "duration": 4,
        "genres": ["Animation", "Action", "Adventure"],
        "director": "Daniel Martinez Lara",
        "cast": ["Daniel Martinez Lara"],
        "language": "No dialogue",
        "country": "Netherlands",
        "quality": "4K",
        "imdb": 7.1,
        "license_note": "CC BY 4.0 — Blender Foundation",
        "video": "",
        "trailer": "https://www.youtube.com/embed/pKmSdY56VtY",
        "featured": False,
        "colors": ("#311b92", "#9fa8da"),
        "description": (
            "Grease Pencil texnikasida chizilgan, 2D va 3D ni birlashtirgan "
            "qisqa film. Qahramon o'z shahrini himoya qilish uchun kurashadi, "
            "har bir kadr qo'lda chizilgandek ko'rinadi."
        ),
    },
    {
        "title": "Coffee Run",
        "year": 2020,
        "duration": 4,
        "genres": ["Animation", "Drama"],
        "director": "Hjalti Hjalmarsson",
        "cast": ["Hjalti Hjalmarsson"],
        "language": "No dialogue",
        "country": "Netherlands",
        "quality": "FHD",
        "imdb": 7.3,
        "license_note": "CC BY 4.0 — Blender Foundation",
        "video": "",
        "trailer": "https://www.youtube.com/embed/JgxlIJIsMk0",
        "featured": False,
        "colors": ("#3e2723", "#bcaaa4"),
        "description": (
            "Qahva bilan quvvat olib yashayotgan qiz kunlik yugurishida "
            "o'tmishi bilan yuzlashadi. Eevee dvigatelida real vaqtda "
            "render qilingan birinchi ochiq film."
        ),
    },
    {
        "title": "Charge",
        "year": 2022,
        "duration": 4,
        "genres": ["Animation", "Sci-Fi", "Thriller"],
        "director": "Francesco Siddi",
        "cast": ["Francesco Siddi"],
        "language": "English",
        "country": "Netherlands",
        "quality": "4K",
        "imdb": 6.9,
        "license_note": "CC BY 4.0 — Blender Foundation",
        "video": "",
        "trailer": "https://www.youtube.com/embed/UXqq0ZvbOnk",
        "featured": False,
        "colors": ("#1a237e", "#7986cb"),
        "description": (
            "Kelajakdagi harbiy operatsiya davomida askar quvvat manbasini "
            "himoya qilishi kerak. Blender Studio ning eng texnik jihatdan "
            "murakkab qisqa loyihalaridan biri."
        ),
    },
]


class Command(BaseCommand):
    help = "Test uchun janr, davlat, til, shaxs va public-domain filmlar yaratadi."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Avval mavjud filmlarni o'chirib, keyin qayta yaratadi.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            deleted, _ = Movie.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"{deleted} ta yozuv o'chirildi."))

        genres = self._create_genres()
        countries = self._create_countries()
        languages = self._create_languages()
        directors, actors = self._create_people()

        created_count = 0
        for data in MOVIES:
            movie, created = self._create_movie(data, genres, countries, languages, directors, actors)
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"  + {movie.title}"))
            else:
                self.stdout.write(f"  = {movie.title} (allaqachon mavjud)")

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Tayyor. {created_count} ta yangi film qo'shildi, "
                f"jami {Movie.objects.count()} ta."
            )
        )
        self.stdout.write(
            "Barcha filmlar Creative Commons litsenziyasi ostidagi Blender "
            "Foundation ochiq loyihalari."
        )

    # -- Ma'lumotnomalar --------------------------------------------------

    def _create_genres(self):
        result = {}
        for name, icon, order in GENRES:
            genre, _ = Genre.objects.get_or_create(
                name=name, defaults={"icon": icon, "order": order}
            )
            result[name] = genre
        self.stdout.write(f"Janrlar: {len(result)} ta")
        return result

    def _create_countries(self):
        result = {}
        for name, code in COUNTRIES:
            country, _ = Country.objects.get_or_create(name=name, defaults={"code": code})
            result[name] = country
        self.stdout.write(f"Davlatlar: {len(result)} ta")
        return result

    def _create_languages(self):
        result = {}
        for name, code in LANGUAGES:
            language, _ = Language.objects.get_or_create(name=name, defaults={"code": code})
            result[name] = language
        self.stdout.write(f"Tillar: {len(result)} ta")
        return result

    def _create_people(self):
        directors = {}
        actors = {}
        for full_name in PEOPLE:
            directors[full_name], _ = Director.objects.get_or_create(full_name=full_name)
            actors[full_name], _ = Actor.objects.get_or_create(full_name=full_name)
        self.stdout.write(f"Rejissyorlar: {len(directors)} ta, aktyorlar: {len(actors)} ta")
        return directors, actors

    # -- Film -------------------------------------------------------------

    def _get_director(self, name, cache):
        if name not in cache:
            cache[name], _ = Director.objects.get_or_create(full_name=name)
        return cache[name]

    def _get_actor(self, name, cache):
        if name not in cache:
            cache[name], _ = Actor.objects.get_or_create(full_name=name)
        return cache[name]

    def _create_movie(self, data, genres, countries, languages, directors, actors):
        existing = Movie.objects.filter(title=data["title"]).first()
        if existing:
            return existing, False

        has_video = bool(data["video"])
        movie = Movie(
            title=data["title"],
            description=data["description"],
            release_year=data["year"],
            duration_minutes=data["duration"],
            quality=data["quality"],
            imdb_rating=data["imdb"],
            trailer_url=data["trailer"],
            video_url=data["video"],
            # Video manbasi bo'lganlar to'liq ko'rish uchun ochiq,
            # qolganlari faqat treyler bilan cheklanadi.
            license_type=(
                Movie.LicenseType.PUBLIC_DOMAIN if has_video else Movie.LicenseType.TRAILER_ONLY
            ),
            license_note=data["license_note"],
            # CC BY litsenziyasi yuklab olishga ham ruxsat beradi.
            is_download_allowed=has_video,
            download_url=data["video"] if has_video else "",
            language=languages.get(data["language"]),
            is_featured=data["featured"],
            is_published=True,
            views_count=random.randint(120, 9800),
        )

        poster = self._render_poster(data)
        if poster:
            movie.poster.save(f"{data['title'][:40]}-poster.png", poster, save=False)

        backdrop = self._render_backdrop(data)
        if backdrop:
            movie.backdrop.save(f"{data['title'][:40]}-backdrop.png", backdrop, save=False)

        movie.save()

        movie.genres.set([genres[g] for g in data["genres"] if g in genres])
        movie.directors.set([self._get_director(data["director"], directors)])
        country = countries.get(data["country"])
        movie.countries.set([country] if country else [])

        for order, actor_name in enumerate(data["cast"]):
            MovieCast.objects.create(
                movie=movie,
                actor=self._get_actor(actor_name, actors),
                character_name="",
                order=order,
            )

        return movie, True

    # -- Placeholder rasmlar ----------------------------------------------

    def _render_poster(self, data):
        """Film uchun 500x750 gradient poster chizadi (tashqi manbasiz)."""
        return self._render_image(data, 500, 750, title_size=44)

    def _render_backdrop(self, data):
        """Hero bo'limi uchun 1600x900 gradient backdrop chizadi."""
        return self._render_image(data, 1600, 900, title_size=86)

    def _render_image(self, data, width, height, title_size):
        if Image is None:
            return None

        start, end = data["colors"]
        start_rgb = self._hex_to_rgb(start)
        end_rgb = self._hex_to_rgb(end)

        image = Image.new("RGB", (width, height), start_rgb)
        draw = ImageDraw.Draw(image)

        # Diagonalga yaqin vertikal gradient.
        for y in range(height):
            ratio = y / max(height - 1, 1)
            color = tuple(
                int(start_rgb[i] + (end_rgb[i] - start_rgb[i]) * ratio) for i in range(3)
            )
            draw.line([(0, y), (width, y)], fill=color)

        # Pastki qismni qoraytiramiz — matn o'qilishi uchun.
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        for y in range(height // 2, height):
            ratio = (y - height // 2) / max(height // 2, 1)
            overlay_draw.line([(0, y), (width, y)], fill=(0, 0, 0, int(230 * ratio)))
        image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(image)

        font = self._load_font(title_size)
        small_font = self._load_font(max(title_size // 3, 14))

        margin = width // 12
        title = data["title"]
        draw.text((margin, height - margin - title_size * 2), title, font=font, fill=(255, 255, 255))
        draw.text(
            (margin, height - margin - title_size // 2),
            f"{data['year']} · {data['quality']} · MORE-MOVIE",
            font=small_font,
            fill=(229, 9, 20),
        )

        buffer = io.BytesIO()
        image.save(buffer, format="PNG", optimize=True)
        return ContentFile(buffer.getvalue())

    @staticmethod
    def _hex_to_rgb(value):
        value = value.lstrip("#")
        return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))

    @staticmethod
    def _load_font(size):
        """Tizim shriftini topishga urinadi, topolmasa standart shriftga qaytadi."""
        for candidate in ("arialbd.ttf", "arial.ttf", "DejaVuSans-Bold.ttf"):
            try:
                return ImageFont.truetype(candidate, size)
            except (OSError, AttributeError):
                continue
        return ImageFont.load_default()
