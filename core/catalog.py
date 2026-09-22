"""Umumiy katalog — kino, multfilm va seriallar uchun YAGONA filtr.

Nega alohida modul: filtr bir vaqtning o'zida ikkita modelga (`Movie` va
`Series`) tegadi, shuning uchun u `movies` yoki `series` ilovasiga
tegishli emas.

Ishlash tartibi:

1. Har bir model uchun bir xil filtrlar qo'llanadi (`_filter_movies`,
   `_filter_series`). Ikkala modelda ham `genres`, `country`, `language`,
   `release_year`, `imdb_rating`, `views_count`, `avg_rating` bor, shu
   sababli filtr va saralash maydonlari aynan bir xil nomlanadi.

2. «Hammasi» tanlanganda ikkita queryset birlashtiriladi. To'liq
   obyektlarni emas, faqat `(pk, saralash kaliti)` juftliklari olinadi --
   shu bilan minglab yozuvni xotiraga yuklamasdan aralash tartiblash
   mumkin bo'ladi.

3. Sahifalash shu yengil ro'yxat ustida bajariladi, so'ng FAQAT joriy
   sahifadagi pk'lar bo'yicha to'liq obyektlar `with_relations()` bilan
   olinadi -- kartalarda N+1 so'rov bo'lmaydi.
"""

from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Count, F, Q
from django.urls import reverse
from django.views.generic import TemplateView

from movies.models import Genre, Movie
from series.models import Series

#: Katalogdagi kontent turlari. Kalit -- URL dagi `?type=` qiymati.
#: (yorliq, ikonka) -- filtr tugmalari uchun.
CONTENT_TYPES = {
    "all": ("Hammasi", "grid"),
    "movie": ("Kinolar", "film"),
    "cartoon": ("Multfilmlar", "sparkle"),
    "series": ("Seriallar", "tv"),
}

#: Saralash tanlovi -> (model maydoni, yorliq, teskarimi).
#: Maydon nomi ikkala modelda ham bir xil bo'lishi SHART -- «hammasi»
#: rejimida aralash tartiblash shunga tayanadi.
SORT_OPTIONS = {
    "latest": ("created_at", "Eng yangi", True),
    "popular": ("views_count", "Eng mashhur", True),
    "rating": ("avg_rating", "Yuqori reyting", True),
    "year": ("release_year", "Yil bo'yicha", True),
    "az": ("title", "A-Z", False),
}

DEFAULT_SORT = "latest"

#: «Hammasi» rejimida aralashtirish uchun har bir modeldan olinadigan
#: maksimal yozuv soni. Katalog bundan kattalashsa ham sahifalash
#: ishlayveradi, shunchaki eng oxirgi sahifalar kesiladi.
MERGE_CAP = 2000


class CatalogView(TemplateView):
    """Kino / multfilm / serial -- bitta filtr, bitta natijalar to'ri."""

    template_name = "core/catalog.html"

    # ------------------------------------------------------------------ filtr

    @staticmethod
    def _parse_multi(raw):
        """"2014,2024,,2014" -> ["2014", "2024"].

        Yil va janr endi BIR NECHTA qiymatni birga qabul qiladi (masalan
        foydalanuvchi 2014 VA 2024 yillarini birga ko'rishni xohlashi
        mumkin) — shuning uchun URL'da vergul bilan ajratilgan ro'yxat
        sifatida saqlanadi (`?year=2014,2024`). Bo'sh bo'lak va
        takrorlar olib tashlanadi, lekin tartib saqlanadi (chiplar
        qatorida ahamiyati yo'q, lekin natija deterministik bo'lsin).
        """
        seen = []
        for piece in raw.split(","):
            piece = piece.strip()
            if piece and piece not in seen:
                seen.append(piece)
        return seen

    def _params(self):
        """URL parametrlarini tozalab, lug'at holida qaytaradi."""
        params = self.request.GET
        content_type = params.get("type", "all")
        if content_type not in CONTENT_TYPES:
            content_type = "all"

        sort = params.get("sort", DEFAULT_SORT)
        if sort not in SORT_OPTIONS:
            sort = DEFAULT_SORT

        return {
            "type": content_type,
            "q": params.get("q", "").strip(),
            # Ikkalasi ham RO'YXAT -- bir nechta yil/janr birga tanlanishi
            # mumkin (masalan `?genre=action,drama&year=2014,2024`).
            "genre": self._parse_multi(params.get("genre", "")),
            "year": self._parse_multi(params.get("year", "")),
            "country": params.get("country", ""),
            "language": params.get("language", ""),
            "rating": params.get("rating", ""),
            "sort": sort,
        }

    def _apply_common(self, queryset, current, search_fields):
        """Ikkala model uchun bir xil bo'lgan filtrlar."""
        if query := current["q"]:
            condition = Q()
            for field in search_fields:
                condition |= Q(**{f"{field}__icontains": query})
            queryset = queryset.filter(condition).distinct()

        # Bir nechta janr/yil OR (birlashma) mantig'ida ishlaydi: masalan
        # `genre=action,drama` bo'lsa Action YOKI Drama janridagi barcha
        # kontent chiqadi -- AND (ikkalasi ham bo'lishi shart) emas, aks
        # holda kamdan-kam filmda ikkala janr birga uchraydi va natija
        # deyarli har doim bo'sh bo'lib qolardi. Xuddi shu sabab yillar
        # uchun ham: bitta film bir nechta yilda chiqmaydi, shuning uchun
        # "2014 VA 2024" so'ragan foydalanuvchi aslida "2014 YOKI 2024"ni
        # nazarda tutadi.
        if genres := current["genre"]:
            queryset = queryset.filter(genres__slug__in=genres).distinct()

        if years := current["year"]:
            valid_years = [int(year) for year in years if year.isdigit()]
            if valid_years:
                queryset = queryset.filter(release_year__in=valid_years)

        if country := current["country"]:
            queryset = queryset.filter(countries__slug=country)

        if language := current["language"]:
            queryset = queryset.filter(language__slug=language)

        if rating := current["rating"]:
            try:
                queryset = queryset.filter(imdb_rating__gte=float(rating))
            except ValueError:
                pass

        return queryset

    def _movie_queryset(self, current):
        """Filtrlangan filmlar. `None` -- bu tur umuman so'ralmagan."""
        if current["type"] == "series":
            return None

        queryset = Movie.objects.published()

        if current["type"] in ("movie", "cartoon"):
            queryset = queryset.of_kind(current["type"])

        return self._apply_common(
            queryset,
            current,
            ["title", "original_title", "description", "genres__name", "directors__full_name"],
        )

    def _series_queryset(self, current):
        """Filtrlangan seriallar. `None` -- bu tur so'ralmagan."""
        # Multfilm/kino tanlangan bo'lsa seriallar chiqmaydi.
        if current["type"] in ("movie", "cartoon"):
            return None

        return self._apply_common(
            Series.objects.published(),
            current,
            ["title", "original_title", "description", "genres__name"],
        )

    # ------------------------------------------------------- natijalar ro'yxati

    def _merged_rows(self, movie_qs, series_qs, sort):
        """`(model_nomi, pk, saralash_kaliti)` uchligidan iborat tartiblangan ro'yxat."""
        field, _label, reverse = SORT_OPTIONS[sort]
        rows = []

        if movie_qs is not None:
            rows += [
                ("movie", pk, key)
                for pk, key in movie_qs.values_list("pk", field)[:MERGE_CAP]
            ]
        if series_qs is not None:
            rows += [
                ("series", pk, key)
                for pk, key in series_qs.values_list("pk", field)[:MERGE_CAP]
            ]

        # `None` qiymatlar (masalan reytingsiz yozuv) tartiblashni buzmasligi
        # uchun eng oxiriga tushadi.
        def sort_key(row):
            value = row[2]
            return (value is None, value if value is not None else 0)

        rows.sort(key=sort_key, reverse=reverse)
        return rows

    def _load_page(self, rows):
        """Joriy sahifadagi pk'lar bo'yicha to'liq obyektlarni yuklaydi."""
        movie_ids = [pk for kind, pk, _ in rows if kind == "movie"]
        series_ids = [pk for kind, pk, _ in rows if kind == "series"]

        movies = {}
        if movie_ids:
            movies = {
                obj.pk: obj
                for obj in Movie.objects.with_relations().filter(pk__in=movie_ids)
            }

        series = {}
        if series_ids:
            series = {
                obj.pk: obj
                for obj in Series.objects.with_relations().filter(pk__in=series_ids)
            }

        # Tartib `rows` dan olinadi -- `filter(pk__in=...)` uni saqlamaydi.
        items = []
        for kind, pk, _ in rows:
            obj = movies.get(pk) if kind == "movie" else series.get(pk)
            if obj is not None:
                items.append({"kind": kind, "object": obj})
        return items

    # ---------------------------------------------------------------- kontekst

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current = self._params()

        movie_qs = self._movie_queryset(current)
        series_qs = self._series_queryset(current)

        rows = self._merged_rows(movie_qs, series_qs, current["sort"])
        paginator = Paginator(rows, settings.MOVIES_PER_PAGE)
        page_obj = paginator.get_page(self.request.GET.get("page"))

        # Sahifalash havolalarida joriy filtrlar saqlanadi.
        params = self.request.GET.copy()
        params.pop("page", None)

        context.update(
            {
                "items": self._load_page(page_obj.object_list),
                "page_obj": page_obj,
                "paginator": paginator,
                "is_paginated": page_obj.has_other_pages(),
                "querystring": params.urlencode(),
                "current": current,
                "type_label": CONTENT_TYPES[current["type"]][0],
                "year_rail": self._year_rail(current),
                "genre_rail": self._genre_rail(current),
                # Bir nechta yil/janr tanlanganda "hammasini tozalash"
                # havolasi uchun -- rail shablonlari `current.year`/
                # `current.genre` orqali qachon ko'rsatishni biladi.
                "year_clear_url": self._clear_url("year"),
                "genre_clear_url": self._clear_url("genre"),
            }
        )
        return context

    def _available_years(self):
        """Filtr ro'yxatidagi yillar -- ikkala katalogdan birlashtirilgan."""
        movie_years = Movie.objects.published().values_list("release_year", flat=True)
        series_years = Series.objects.published().values_list("release_year", flat=True)
        return sorted({year for year in list(movie_years) + list(series_years) if year}, reverse=True)

    def _toggle_url(self, key, value, selected):
        """Bitta qiymatni RO'YXATGA qo'shadi yoki undan olib tashlaydi.

        Eski `_switch_url` butun qiymatni almashtirardi (bir vaqtda
        faqat bitta yil/janr mumkin edi). Bu esa checkbox kabi ishlaydi:
        qiymat allaqachon tanlangan bo'lsa o'chadi, aks holda ro'yxatga
        qo'shiladi -- qolgan tanlovlar (va boshqa filtrlar) saqlanib
        qoladi.
        """
        value = str(value)
        updated = [item for item in selected if item != value] if value in selected else [*selected, value]

        params = self.request.GET.copy()
        params.pop("page", None)
        if updated:
            params[key] = ",".join(updated)
        else:
            params.pop(key, None)
        return f"{reverse('core:catalog')}?{params.urlencode()}"

    def _clear_url(self, key):
        """Bitta filtrni (masalan barcha tanlangan yillarni) butunlay o'chiradi."""
        params = self.request.GET.copy()
        params.pop("page", None)
        params.pop(key, None)
        return f"{reverse('core:catalog')}?{params.urlencode()}"

    def _year_rail(self, current):
        """Tezkor yil tanlash qatori — bir nechtasi birga faol bo'lishi mumkin.

        Ilgari faqat YIL filtri allaqachon faol bo'lganda ko'rsatilardi.
        Endi bu qator yagona kirish nuqtasi bo'lgani uchun (alohida
        filtr formasi yo'q) DOIM ko'rsatiladi -- aks holda foydalanuvchi
        birinchi yilni tanlashning iloji bo'lmasdi.
        """
        years = self._available_years()
        if not years:
            return None
        return [
            {
                "year": year,
                "url": self._toggle_url("year", year, current["year"]),
                "active": str(year) in current["year"],
            }
            for year in years
        ]

    def _genre_rail(self, current):
        """Tezkor janr tanlash qatori — bir nechtasi birga faol bo'lishi mumkin.

        Kino, multfilm va serial BIRGA hisoblanadi -- katalog
        uchchalasini ham qamrab oladi. `_year_rail` bilan bir xil sabab:
        DOIM ko'rsatiladi, aks holda birinchi janrni tanlab bo'lmasdi.
        """
        genres = list(
            Genre.objects.annotate(
                movie_total=Count("movies", filter=Q(movies__is_published=True), distinct=True),
                series_total=Count("series", filter=Q(series__is_published=True), distinct=True),
            )
            .annotate(total=F("movie_total") + F("series_total"))
            .filter(total__gt=0)
            .order_by("-total", "name")
        )
        if not genres:
            return None
        return [
            {
                "genre": genre,
                "url": self._toggle_url("genre", genre.slug, current["genre"]),
                "active": genre.slug in current["genre"],
            }
            for genre in genres
        ]
