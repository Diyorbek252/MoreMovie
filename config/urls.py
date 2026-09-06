"""MORE-MOVIE — asosiy URL router.

Tartib muhim: `movies.urls` da `movie/<slug>/` kabi aniq prefiksli yo'llar
bor, `core.urls` esa bo'sh yo'lni (`""`) egallaydi — shuning uchun core
oxirida turadi.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.generic import TemplateView

from core.sitemaps import GenreSitemap, MovieSitemap, StaticSitemap

sitemaps = {
    "movies": MovieSitemap,
    "genres": GenreSitemap,
    "static": StaticSitemap,
}

urlpatterns = [
    path("admin/", admin.site.urls),

    path("", include("users.urls")),
    path("", include("movies.urls")),
    path("", include("reviews.urls")),
    path("dashboard/", include("dashboard.urls")),

    # --- SEO ---
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
        name="robots",
    ),

    # Bo'sh yo'lni egallagani uchun eng oxirida.
    path("", include("core.urls")),
]

# Xato sahifalari — DEBUG=False bo'lganda ishlaydi.
handler404 = "core.views.error_404"
handler403 = "core.views.error_403"
handler500 = "core.views.error_500"

if settings.DEBUG:
    # Development'da media fayllarni Django o'zi xizmat qiladi.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
