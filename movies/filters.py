"""Film ro'yxati uchun django-filter to'plami.

`core/catalog.py` dagi `CatalogView._params()`/`_apply_common()` bilan bir
xil maydon nomlari va mantiq ishlatiladi — Next.js frontend eski
`/katalog/?genre=..&year=..` querystring shaklini deyarli o'zgarishsiz
`/api/v1/movies/?genre=..&year=..` ga yuborishi mumkin.
"""

import django_filters as filters

from .models import Movie


class MovieFilter(filters.FilterSet):
    genre = filters.CharFilter(field_name="genres__slug")
    country = filters.CharFilter(field_name="countries__slug")
    language = filters.CharFilter(field_name="language__slug")
    year = filters.NumberFilter(field_name="release_year")
    rating = filters.NumberFilter(field_name="imdb_rating", lookup_expr="gte")
    kind = filters.ChoiceFilter(choices=Movie.Kind.choices)

    class Meta:
        model = Movie
        fields = ["genre", "country", "language", "year", "rating", "kind"]
