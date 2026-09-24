"""DRF API router — `/api/v1/`.

Har bir ilova o'z `api_v1_urls.py` moduliga ega (mavjud `api.py` bilan
to'qnashmasligi uchun alohida nom). Eski, shablon asosidagi `urls.py` lar
(`movies.urls`, `reviews.urls` va h.k.) va ulardagi `/api/search/`,
`/api/rate/` kabi eski endpointlar o'zgarishsiz ishlab turadi — bu yerdagi
`v1` marshrutlari ular bilan to'qnashmaydi (CLAUDE.md rejasi, 6-bosqichgacha).
"""

from django.urls import include, path

urlpatterns = [
    path("", include("core.api_v1_urls")),
    path("", include("users.api_v1_urls")),
    path("", include("movies.api_v1_urls")),
    path("", include("series.api_v1_urls")),
    path("", include("reviews.api_v1_urls")),
    path("", include("shop.api_v1_urls")),
    path("", include("siteconfig.api_v1_urls")),
    path("", include("subscriptions.api_v1_urls")),
]

try:  # pragma: no cover - ixtiyoriy, faqat drf-spectacular o'rnatilgan bo'lsa
    from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

    urlpatterns += [
        path("schema/", SpectacularAPIView.as_view(), name="schema"),
        path(
            "schema/swagger-ui/",
            SpectacularSwaggerView.as_view(url_name="schema"),
            name="swagger-ui",
        ),
    ]
except ImportError:
    pass
