"""DRF API — bosh sahifa, umumiy katalog (Movie+Series), murojaat formasi.

`HomeView`/`CatalogView` (`core/views.py`, `core/catalog.py`) dagi filtr,
keshlash va aralashtirib-saralash mantig'i QAYTA YOZILMAYDI — bu ikki
klass to'g'ridan-to'g'ri (shablonsiz) ishlatiladi, natija esa DRF
serializerlari orqali JSON'ga o'raladi. Shu bilan HTML va API doim bir
xil natija berishi kafolatlanadi.
"""

from django.conf import settings
from rest_framework import permissions
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from movies.serializers import GenreSerializer, MovieCardSerializer
from series.serializers import SeriesCardSerializer

from .catalog import CatalogView
from .serializers import ContactSerializer
from .views import HomeView


class HomeAPIView(APIView):
    """`GET /api/v1/home/` — `HomeView.get_context_data` bilan bir xil ma'lumot."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        helper = HomeView()
        helper.request = request
        context = helper.get_context_data()
        req_ctx = {"request": request}

        hero = context.get("hero")
        hero_data = MovieCardSerializer(hero, context=req_ctx).data if hero else None

        rail_sections = []
        for section in context["rail_sections"]:
            key = section["key"]
            raw_items = section["movies"]
            # "genres" va "years" bo'limlari Movie/Series emas — Genre
            # obyektlari va oddiy yil raqamlari (qarang: HomeView.RAIL_CONFIG,
            # HomeView._get_shared_sections).
            if key == "genres":
                items = GenreSerializer(raw_items, many=True, context=req_ctx).data
            elif key == "years":
                items = list(raw_items)
            elif section["is_series"]:
                items = SeriesCardSerializer(raw_items, many=True, context=req_ctx).data
            else:
                items = MovieCardSerializer(raw_items, many=True, context=req_ctx).data

            rail_sections.append(
                {
                    "key": key,
                    "title": section["title"],
                    "subtitle": section["subtitle"],
                    "link": section["link"],
                    "is_series": section["is_series"],
                    "items": items,
                }
            )

        continue_watching = []
        for entry in context.get("continue_watching", []):
            item = MovieCardSerializer(entry.movie, context=req_ctx).data
            item["resume_seconds"] = entry.progress_seconds
            item["progress_percent"] = entry.progress_percent
            continue_watching.append(item)

        return Response(
            {
                "hero": hero_data,
                "rail_sections": rail_sections,
                "continue_watching": continue_watching,
            }
        )


class CatalogAPIView(APIView):
    """`GET /api/v1/catalog/?type=..&q=..&genre=..&year=..&sort=..`

    `core/catalog.py::CatalogView` bilan AYNAN bir xil filtr/sort/merge
    mantig'i — parametr nomlari eskisi bilan bir xil, Next.js eski
    `/katalog/?...` querystring'ini deyarli o'zgarishsiz shu yerga
    yuborishi mumkin.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        helper = CatalogView()
        helper.request = request
        current = helper._params()

        movie_qs = helper._movie_queryset(current)
        series_qs = helper._series_queryset(current)
        rows = helper._merged_rows(movie_qs, series_qs, current["sort"])

        paginator = PageNumberPagination()
        paginator.page_size = settings.MOVIES_PER_PAGE
        page_rows = paginator.paginate_queryset(rows, request, view=self)
        items = helper._load_page(page_rows)

        req_ctx = {"request": request}
        data = []
        for item in items:
            if item["kind"] == "movie":
                payload = MovieCardSerializer(item["object"], context=req_ctx).data
            else:
                payload = SeriesCardSerializer(item["object"], context=req_ctx).data
            data.append({"kind": item["kind"], **payload})

        from .catalog import CONTENT_TYPES

        response = paginator.get_paginated_response(data)
        response.data["current"] = current
        response.data["type_label"] = CONTENT_TYPES[current["type"]][0]
        # Yil tanlash qatori uchun — HTML katalogdagi `year_rail` bilan bir
        # xil manba (kino va seriallar birga, yangisidan eskisiga).
        response.data["available_years"] = helper._available_years()
        return response


class ContactView(APIView):
    """`POST /api/v1/contact/` — `core/forms.py::ContactForm` DRF ekvivalenti."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ContactSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Xabaringiz yuborildi. Tez orada siz bilan bog'lanamiz."})
