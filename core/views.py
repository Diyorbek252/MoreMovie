"""Sayt darajasidagi sahifalar: home, about, contact, huquqiy sahifalar."""

import mimetypes
import re
from pathlib import Path

from django.contrib import messages
from django.core.cache import cache
from django.db.models import Count, Q
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseNotModified,
    StreamingHttpResponse,
)
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils._os import safe_join
from django.utils.http import http_date
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView
from django.views.static import was_modified_since

from movies.models import Genre, Movie, ViewHistory
from series.models import Series
from siteconfig.models import HomepageSection

from .forms import ContactForm

# Bosh sahifa bo'limlarini keshlash muddati (soniya).
HOME_CACHE_TTL = 300

# Xom (keshlangan) ro'yxatlar shuncha uzunlikda olib kelinadi -- shu bilan
# admin `HomepageSection.item_limit` ni katta qiymatga o'zgartirsa ham
# (forma 50 gacha ruxsat beradi), keshni qayta hisoblamasdan yetarli
# element bo'ladi. Faktik ko'rsatiladigan son har doim `item_limit` bilan
# kesiladi -- bu yerda faqat "zaxira hovuz" hajmi.
RAW_POOL_SIZE = 50


class HomeView(TemplateView):
    """Bosh sahifa — hero + bir nechta karusel bo'lim.

    Har bir bo'lim admin panelidan (`HomepageSection`) yoqilishi/
    o'chirilishi, sarlavhasi va elementlar soni o'zgartirilishi mumkin.

    MUHIM -- orqaga moslik: agar `HomepageSection` jadvali umuman bo'sh
    bo'lsa (masalan `seed_homepage_sections` hali ishga tushirilmagan),
    sahifa aynan HomepageSection joriy etilishidan OLDINGI xatti-harakatni
    saqlaydi -- barcha bo'lim ko'rinadi, standart sarlavha/tartib/limit
    ishlatiladi. Shuning uchun bu funksiya hech qachon sayt tashqi
    ko'rinishini "bo'sh konfiguratsiya" sababli buzmaydi.

    Hero va "Davom ettirish" shablonda maxsus (qat'iy) joylashuvga ega --
    ular faqat yoqilgan/o'chirilgan holatini o'zgartira oladi, sahifadagi
    o'rnini emas. Qolgan bo'limlar (Premyeralar, Kinolar, Multfilmlar,
    Seriallar, Janrlar) esa `HomepageSection.order` bo'yicha TO'LIQ qayta
    tartiblanadi.

    Bo'limlar kontent TURI bo'yicha ajratilgan ("trending"/"popular" kabi
    o'lchovlar bo'yicha emas) -- har bir bo'lim umumiy katalogning
    (`core:catalog`) tegishli filtriga olib boradi.
    """

    template_name = "core/home.html"

    #: (kalit, standart sarlavha, standart limit, katalogdagi filtr).
    #: Oxirgi element -- "Barchasini ko'rish" havolasining query qismi.
    #: Premyeralar uchun `link_suffix` yo'q (`None`) — bu bo'lim umumiy
    #: katalogda alohida filtrga ega emas, shuning uchun "Barchasini
    #: ko'rish" havolasi ko'rsatilmaydi (qarang: get_context_data).
    RAIL_CONFIG = [
        ("premieres", "Premyeralar", 14, None),
        ("movies", "Kinolar", 14, "?type=movie"),
        ("cartoons", "Multfilmlar", 14, "?type=cartoon"),
        ("series", "Seriallar", 14, "?type=series"),
        # Janrlar va yillar ham gorizontal karusel — to'rda emas, shuning
        # uchun limit kattaroq bo'lishi mumkin (ortiqchasi surib ko'riladi).
        ("genres", "Janrlar", 20, ""),
        ("years", "Yillar", 24, ""),
    ]

    #: Serial kartasi boshqa shablon bilan chiziladi (partials/series_card.html).
    SERIES_KEYS = {"series"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shared = self._get_shared_sections()
        data = shared["data"]
        config = shared["config"]

        def is_active(key):
            """Sozlamada yozuv bo'lmasa bo'lim KO'RINADI.

            Yangi bo'lim turi qo'shilganda (masalan «Premyeralar») eski
            konfiguratsiyada uning qatori bo'lmaydi -- shunda bo'lim
            jimgina yo'qolib qolmasligi kerak. Yashirish faqat admin
            aniq o'chirganda bo'ladi.
            """
            row = config.get(key)
            return row.is_active if row else True

        def item_limit(key, default):
            row = config.get(key)
            return row.item_limit if row else default

        def title(key, default):
            row = config.get(key)
            return row.title if row and row.title else default

        def subtitle(key):
            row = config.get(key)
            return row.subtitle if row else ""

        context["hero"] = data["hero"] if is_active("hero") else None

        # Tartib. Sozlamada qatori bor bo'lim o'z `order` qiymatida turadi;
        # qatori YO'Q yangi bo'lim (masalan «Yillar») RAIL_CONFIG da o'zidan
        # oldin turgan bo'limdan keyingi joyni oladi.
        #
        # RAIL_CONFIG indeksiga qaytish XATO bo'lardi: bazadagi qiymatlar
        # 0, 10, 20 ... qadam bilan yoziladi, ya'ni indeksdan ancha katta --
        # shunda qatori yo'q yangi bo'lim sahifaning eng TEPASIGA sakrab
        # chiqib ketadi. Boshlang'ich nuqta -- rail bo'lmagan bo'limlarning
        # (hero, davom ettirish) eng katta tartibi.
        rail_keys = {key for key, *_ in self.RAIL_CONFIG}
        previous_order = max(
            (row.order for key, row in config.items() if key not in rail_keys),
            default=-1,
        )
        effective_order = {}
        for key, *_ in self.RAIL_CONFIG:
            row = config.get(key)
            previous_order = float(row.order) if row else previous_order + 0.5
            effective_order[key] = previous_order

        catalog_url = reverse("core:catalog")
        rail_sections = []
        for key, default_title, default_limit, link_suffix in self.RAIL_CONFIG:
            if not is_active(key):
                continue
            rail_sections.append(
                {
                    "key": key,
                    "title": title(key, default_title),
                    "subtitle": subtitle(key),
                    "movies": data.get(key, [])[: item_limit(key, default_limit)],
                    "is_series": key in self.SERIES_KEYS,
                    "link": (
                        reverse("movies:genre_list")
                        if key == "genres"
                        else (catalog_url + link_suffix if link_suffix is not None else "")
                    ),
                    "order": effective_order[key],
                }
            )
        rail_sections.sort(key=lambda section: section["order"])
        context["rail_sections"] = rail_sections

        # Foydalanuvchiga xos bo'lim — keshdan tashqarida, faqat "Davom
        # ettirish" bo'limi (admin tomonidan) yoqilgan VA foydalanuvchi
        # o'zi uni yashirmagan bo'lsagina hisoblanadi (Profile.
        # show_continue_watching — bosh sahifadagi «Yashirish» tugmasi
        # yoki profil sozlamalaridan boshqariladi).
        user = self.request.user
        if is_active("continue") and user.is_authenticated and user.profile.show_continue_watching:
            context["continue_watching"] = (
                ViewHistory.objects.filter(user=user, is_finished=False, progress_seconds__gt=30)
                .select_related("movie", "movie__language")
                .prefetch_related("movie__genres", "movie__directors", "movie__countries")[:12]
            )

        return context

    def _get_shared_sections(self):
        """Umumiy bo'limlarni keshdan oladi, bo'lmasa hisoblab keshga yozadi.

        Kesh ikki qismdan iborat: xom ma'lumot (`data`) va joriy
        `HomepageSection` konfiguratsiyasi (`config`) -- ikkalasi ham
        bitta so'rov turkumida olinadi va birga keshlanadi.
        """
        cached = cache.get("home_sections")
        if cached is not None:
            return cached

        published = Movie.objects.published()

        # Hero uchun: tanlangan filmlar orasidan backdrop'i bori.
        hero = published.with_relations().filter(is_featured=True).exclude(backdrop="").first()
        if hero is None:
            hero = published.with_relations().first()

        data = {
            "hero": hero,
            # Bo'limlar kontent turi bo'yicha -- umumiy katalogdagi
            # `?type=` filtri bilan bir xil bo'linish.
            "premieres": list(Movie.objects.premieres()[:RAW_POOL_SIZE]),
            "movies": list(Movie.objects.films().order_by("-created_at")[:RAW_POOL_SIZE]),
            "cartoons": list(Movie.objects.cartoons().order_by("-created_at")[:RAW_POOL_SIZE]),
            "series": list(Series.objects.newest()[:RAW_POOL_SIZE]),
            # Faqat filmi bor janrlar ko'rsatiladi.
            "genres": list(
                Genre.objects.annotate(
                    movie_total=Count("movies", filter=Q(movies__is_published=True))
                )
                .filter(movie_total__gt=0)
                .order_by("-movie_total")[:20]
            ),
            "years": self._release_years(),
        }

        config = {row.key: row for row in HomepageSection.objects.all()}

        result = {"data": data, "config": config}
        cache.set("home_sections", result, HOME_CACHE_TTL)
        return result

    @staticmethod
    def _release_years():
        """Kamida bitta yozuv chiqqan yillar — yangisidan eskisiga.

        Kino, multfilm va seriallar BIRGA olinadi: foydalanuvchi yilni
        tanlaganda umumiy katalog (`?year=`) ham aynan shu uchchalasini
        qaytaradi, shuning uchun ro'yxat ham shunga mos bo'lishi kerak.

        Bo'limda yozuvlar SONI ko'rsatilmaydi (bu bo'lim yil tanlash
        uchun), shuning uchun agregat emas, oddiy `distinct` yetarli —
        modelga bittadan yengil so'rov.
        """
        years = set()

        for queryset in (Movie.objects.published(), Series.objects.published()):
            years.update(
                queryset.exclude(release_year__isnull=True)
                .values_list("release_year", flat=True)
                .distinct()
            )

        return sorted(years, reverse=True)


class AboutView(TemplateView):
    template_name = "core/about.html"


class PrivacyView(TemplateView):
    template_name = "core/privacy.html"


class TermsView(TemplateView):
    template_name = "core/terms.html"


class ContactView(CreateView):
    """Murojaat formasi — xabar bazaga yoziladi."""

    form_class = ContactForm
    template_name = "core/contact.html"
    success_url = reverse_lazy("core:contact")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            "Xabaringiz yuborildi. Tez orada siz bilan bog'lanamiz.",
        )
        return response

    def form_invalid(self, form):
        messages.error(self.request, "Formada xatolik bor — quyidagilarni tekshiring.")
        return super().form_invalid(form)


# ---------------------------------------------------------------------------
# Xato sahifalari
# ---------------------------------------------------------------------------


def error_404(request, exception=None):
    return render(request, "errors/404.html", status=404)


def error_403(request, exception=None):
    return render(request, "errors/403.html", status=403)


def error_500(request):
    return render(request, "errors/500.html", status=500)


# ---------------------------------------------------------------------------
# Media fayllarni Range so'rovlari bilan xizmat qilish (faqat DEBUG)
# ---------------------------------------------------------------------------

MEDIA_CHUNK_SIZE = 8192
_RANGE_RE = re.compile(r"bytes\s*=\s*(\d*)-(\d*)", re.IGNORECASE)


def _iter_file_range(full_path, start, length, chunk_size=MEDIA_CHUNK_SIZE):
    """Fayldan `start` baytidan boshlab `length` bayt o'qib, bo'laklab beradi."""
    with open(full_path, "rb") as handle:
        handle.seek(start)
        remaining = length
        while remaining > 0:
            chunk = handle.read(min(chunk_size, remaining))
            if not chunk:
                break
            remaining -= len(chunk)
            yield chunk


def serve_media(request, path, document_root=None):
    """`django.views.static.serve()` ning HTTP Range'ni qo'llab-quvvatlaydigan o'rnini bosuvchisi.

    Django'ning standart media serve() funksiyasi (dev rejimida
    `MEDIA_URL` uchun ishlatiladi) `Range` so'rov sarlavhasini umuman
    o'qimaydi va har doim faylni to'liq, boshidan qaytaradi. Video
    elementi esa oldinga o'tkazish (seek) uchun aynan shu sarlavha
    orqali kerakli bayt oralig'ini so'raydi — javob berilmagach,
    brauzer so'ralgan joyga o'ta olmay, oxirgi buferlangan (ko'pincha
    ancha orqadagi) joyga "qaytib qoladi". Bu funksiya xuddi shu
    `static()` yo'l yordamchisi chaqiradigan view sifatida ulanadi
    (`config/urls.py`), imzosi va xatti-harakati mos keladi.

    Ishlab chiqarishda (`DEBUG=False`) media haqiqiy veb-server yoki
    CDN orqali xizmat qilinishi kerak — bu yechim faqat lokal
    ishlanmada video ko'rish/oldinga o'tkazishni to'g'ri ishlashi
    uchun.
    """
    full_path = Path(safe_join(document_root, path))

    if not full_path.is_file():
        raise Http404("Fayl topilmadi.")

    stat_result = full_path.stat()
    file_size = stat_result.st_size

    if not was_modified_since(
        request.META.get("HTTP_IF_MODIFIED_SINCE"), stat_result.st_mtime
    ):
        return HttpResponseNotModified()

    content_type, encoding = mimetypes.guess_type(str(full_path))
    content_type = content_type or "application/octet-stream"

    range_match = _RANGE_RE.match(request.META.get("HTTP_RANGE", ""))

    if range_match:
        start_str, end_str = range_match.groups()
        start = int(start_str) if start_str else 0
        end = int(end_str) if end_str else file_size - 1
        end = min(end, file_size - 1)

        if start >= file_size or start > end:
            response = HttpResponse(status=416, content_type=content_type)
            response.headers["Content-Range"] = f"bytes */{file_size}"
            return response

        length = end - start + 1
        response = StreamingHttpResponse(
            _iter_file_range(full_path, start, length),
            status=206,
            content_type=content_type,
        )
        response.headers["Content-Range"] = f"bytes {start}-{end}/{file_size}"
        response.headers["Content-Length"] = str(length)
    else:
        response = StreamingHttpResponse(
            _iter_file_range(full_path, 0, file_size),
            content_type=content_type,
        )
        response.headers["Content-Length"] = str(file_size)

    response.headers["Accept-Ranges"] = "bytes"
    response.headers["Last-Modified"] = http_date(stat_result.st_mtime)
    if encoding:
        response.headers["Content-Encoding"] = encoding
    return response
