"""sitemap.xml uchun konfiguratsiya."""

from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from movies.models import Genre, Movie


class MovieSitemap(Sitemap):
    """Chop etilgan filmlar — eng muhim SEO sahifalari."""

    changefreq = "weekly"
    priority = 0.9
    protocol = "https"

    def items(self):
        return Movie.objects.published().only("slug", "updated_at")

    def lastmod(self, obj):
        return obj.updated_at


class GenreSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6
    protocol = "https"

    def items(self):
        return Genre.objects.all()

    def lastmod(self, obj):
        return obj.updated_at


class StaticSitemap(Sitemap):
    """Statik sahifalar."""

    changefreq = "monthly"
    priority = 0.5
    protocol = "https"

    def items(self):
        return [
            "core:home",
            "core:about",
            "core:contact",
            "core:privacy",
            "core:terms",
            "core:catalog",
            "movies:genre_list",
        ]

    def location(self, item):
        return reverse(item)
