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
    o'rnini emas. Qolgan oltita bo'lim turi (Trending, Popular, New
    Releases, Top Rated, Janrlar, Featured) esa `HomepageSection.order`
    bo'yicha TO'LIQ qayta tartiblanadi.
    """

    template_name = "core/home.html"

    # (kalit, standart sarlavha, standart limit, qidiruv sahifasiga havola qo'shimchasi)
    RAIL_CONFIG = [
        ("trending", "Trending", 14, "?sort=popular"),
        ("popular", "Popular Movies", 14, "?sort=popular"),
        ("new_releases", "New Releases", 14, "?sort=latest"),
        ("top_rated", "Top Rated", 14, "?sort=rating"),
        ("genres", "Janrlar", 10, ""),
        ("featured", "Featured", 14, ""),
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shared = self._get_shared_sections()
        data = shared["data"]
        config = shared["config"]
        # Konfiguratsiya umuman yo'q bo'lsa — hech narsa yashirilmaydi,
        # bu HomepageSection joriy etilishidan oldingi asl holat.
        has_config = bool(config)

        def is_active(key):
            row = config.get(key)
            return row.is_active if row else not has_config

        def item_limit(key, default):
            row = config.get(key)
            return row.item_limit if row else default

        def title(key, default):
            row = config.get(key)
            return row.title if row and row.title else default

        def subtitle(key):
            row = config.get(key)
            return row.subtitle if row else ""

        def order(key, fallback_index):
            row = config.get(key)
            return row.order if row else fallback_index

        context["hero"] = data["hero"] if is_active("hero") else None

        movies_list_url = reverse("movies:movie_list")
        rail_sections = []
        for index, (key, default_title, default_limit, link_suffix) in enumerate(self.RAIL_CONFIG):
            if not is_active(key):
                continue
            rail_sections.append(
                {
                    "key": key,
                    "title": title(key, default_title),
                    "subtitle": subtitle(key),
                    "movies": data.get(key, [])[: item_limit(key, default_limit)],
                    "link": movies_list_url + link_suffix if key != "genres" else reverse("movies:genre_list"),
                    "order": order(key, index),
                }
            )
        rail_sections.sort(key=lambda section: section["order"])
        context["rail_sections"] = rail_sections

        # Foydalanuvchiga xos bo'lim — keshdan tashqarida, faqat "Davom
        # ettirish" bo'limi yoqilgan bo'lsagina hisoblanadi.
        user = self.request.user
        if is_active("continue") and user.is_authenticated:
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

        trending_pool = list(Movie.objects.trending()[:RAW_POOL_SIZE])

        data = {
            "hero": hero,
            "trending": trending_pool,
            # "Popular" va "Trending" bir xil bo'lmasligi uchun siljitilgan oyna.
            "popular": list(Movie.objects.trending()[14 : 14 + RAW_POOL_SIZE]) or trending_pool,
            "new_releases": list(Movie.objects.newest()[:RAW_POOL_SIZE]),
            "top_rated": list(Movie.objects.top_rated()[:RAW_POOL_SIZE]),
            "featured": list(Movie.objects.featured()[:RAW_POOL_SIZE]),
            # Faqat filmi bor janrlar ko'rsatiladi.
            "genres": list(
                Genre.objects.annotate(
                    movie_total=Count("movies", filter=Q(movies__is_published=True))
                )
                .filter(movie_total__gt=0)
                .order_by("-movie_total")[:20]
            ),
        }

        config = {row.key: row for row in HomepageSection.objects.all()}

        result = {"data": data, "config": config}
        cache.set("home_sections", result, HOME_CACHE_TTL)
        return result


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
