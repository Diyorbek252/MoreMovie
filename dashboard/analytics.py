"""Analitika uchun sof so'rov funksiyalari.

Bu modul view'lardan ATAYLAB ajratilgan: har bir funksiya faqat
parametr(lar) qabul qilib, oddiy Python tuzilma (dict/list) qaytaradi —
`request` bilan ishlamaydi. Shu bilan `AnalyticsView` yupqa qoladi va
funksiyalarni alohida (masalan shell'da) tekshirish oson bo'ladi.

MUHIM: yangi migratsiya YO'Q. Bu yerdagi barcha ko'rsatkichlar mavjud
modellardan (`ViewHistory`, `Movie.views_count`/`downloads_count`,
`User.date_joined` va h.k.) hisoblanadi. Haqiqiy "unique visitors"
(IP/sessiya darajasida) yoki vaqt bo'yicha "downloads" tarixi uchun
alohida event-jadval kerak bo'lardi — buni o'ylab topib ko'rsatish
o'rniga, mavjud ma'lumotdan olinadigan eng yaqin proksi ishlatiladi
(masalan "unique_viewers" — ViewHistory'da hech bo'lmasa bitta yozuvi
bor foydalanuvchilar soni) va bu izohlarda aniq ko'rsatiladi.
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone

from movies.models import Favorite, Genre, Movie, ViewHistory, Watchlist
from reviews.models import Rating, Review
from series.models import Episode, Series

User = get_user_model()

# "Bugun / 7 kun / 30 kun / 3 oy / 1 yil" filtri shu lug'atdan quriladi.
DATE_RANGES = {
    "today": ("Bugun", 1),
    "7d": ("7 kun", 7),
    "30d": ("30 kun", 30),
    "90d": ("3 oy", 90),
    "365d": ("1 yil", 365),
}
DEFAULT_RANGE = "30d"


def resolve_range(range_key):
    """GET parametridan xavfsiz kunlar soniga o'tadi -- noma'lum kalitda standart qiymat."""
    if range_key not in DATE_RANGES:
        range_key = DEFAULT_RANGE
    label, days = DATE_RANGES[range_key]
    return range_key, label, days


def _daily_series(queryset, date_field, days):
    """Berilgan querysetni kunlar bo'yicha guruhlab, nol bilan to'ldirilgan
    ``[{"label": "12/03", "value": n}, ...]`` ro'yxatini qaytaradi.

    ``DashboardIndexView._daily_views`` bilan bir xil naqsh -- shu yerga
    ko'chirilgan va umumiy holatga keltirilgan (istalgan model/sana
    maydoni bilan ishlaydi).
    """
    today = timezone.localdate()
    start = today - timedelta(days=days - 1)

    rows = (
        queryset.filter(**{f"{date_field}__date__gte": start})
        .values(date_field)
        .annotate(total=Count("id"))
    )
    # `values(date_field)` kaliti sana maydoni nomi bilan keladi -- shu
    # kalit ostidagi qiymat aynan sana (vaqtsiz) bo'lishi uchun `__date`
    # qo'shimchasi kerak edi, lekin `.values()` ichida ishlatib bo'lmaydi,
    # shuning uchun Python tomonida qayta guruhlaymiz.
    counts = {}
    for row in rows:
        day = row[date_field]
        day = day.date() if hasattr(day, "date") else day
        counts[day] = counts.get(day, 0) + row["total"]

    return [
        {
            "label": (start + timedelta(days=i)).strftime("%d/%m"),
            "value": counts.get(start + timedelta(days=i), 0),
        }
        for i in range(days)
    ]


def daily_views(days=30):
    """Kunlik ko'rishlar soni (``ViewHistory`` yozuvlari bo'yicha)."""
    return _daily_series(ViewHistory.objects.all(), "watched_at", days)


def user_growth(days=30):
    """Kunlik yangi ro'yxatdan o'tishlar soni."""
    return _daily_series(User.objects.all(), "date_joined", days)


def content_growth(days=30):
    """Kunlik yangi qo'shilgan filmlar soni."""
    return _daily_series(Movie.objects.all(), "created_at", days)


def top_movies(limit=10, metric="views"):
    """Eng ko'p ko'rilgan / yuklab olingan / yuqori baholangan filmlar.

    ``metric``: "views" | "downloads" | "rating"
    """
    queryset = Movie.objects.published().select_related("language").prefetch_related("countries")

    if metric == "downloads":
        return list(queryset.order_by("-downloads_count")[:limit])
    if metric == "rating":
        return list(queryset.filter(rating_count__gt=0).order_by("-avg_rating", "-rating_count")[:limit])
    return list(queryset.order_by("-views_count")[:limit])


def top_series(limit=10):
    """Eng ko'p ko'rilgan seriallar."""
    return list(Series.objects.published().order_by("-views_count")[:limit])


def genre_share(limit=8):
    """Eng ko'p filmga ega janrlar -- ulush diagrammasi uchun."""
    return list(
        Genre.objects.annotate(
            movie_total=Count("movies", filter=Q(movies__is_published=True))
        )
        .filter(movie_total__gt=0)
        .order_by("-movie_total")[:limit]
    )


def rating_distribution():
    """1..5 yulduzlar bo'yicha baholar soni -- har doim 5 ta band bilan (bo'sh bo'lsa 0)."""
    rows = dict(
        Rating.objects.values_list("score").annotate(total=Count("id")).order_by("score")
    )
    return [{"score": score, "count": rows.get(score, 0)} for score in range(1, 6)]


def engagement_summary(days=30):
    """Statistika kartalari uchun umumiy va davr ichidagi ko'rsatkichlar.

    Har bir "davr ichida" ko'rsatkich uchun oldingi xuddi shunday
    davr bilan solishtirilgan foiz o'zgarish ham hisoblanadi
    (masalan 30 kunlik oyna bo'lsa, undan oldingi 30 kun bilan).
    """
    today = timezone.localdate()
    period_start = today - timedelta(days=days - 1)
    prev_start = period_start - timedelta(days=days)
    prev_end = period_start - timedelta(days=1)

    movie_totals = Movie.objects.aggregate(
        views=Sum("views_count"),
        downloads=Sum("downloads_count"),
        avg_rating=Avg("avg_rating", filter=Q(rating_count__gt=0)),
    )

    new_users_current = User.objects.filter(date_joined__date__gte=period_start).count()
    new_users_prev = User.objects.filter(
        date_joined__date__gte=prev_start, date_joined__date__lte=prev_end
    ).count()

    new_movies_current = Movie.objects.filter(created_at__date__gte=period_start).count()
    new_movies_prev = Movie.objects.filter(
        created_at__date__gte=prev_start, created_at__date__lte=prev_end
    ).count()

    views_current = ViewHistory.objects.filter(watched_at__date__gte=period_start).count()
    views_prev = ViewHistory.objects.filter(
        watched_at__date__gte=prev_start, watched_at__date__lte=prev_end
    ).count()

    # "Unique visitors" o'rniga eng yaqin proksi: kamida bitta filmni
    # ko'rgan (ViewHistory yozuvi bor) noyob foydalanuvchilar soni.
    unique_viewers = ViewHistory.objects.values("user_id").distinct().count()
    # "Returning users" proksi: 2 va undan ko'p turli filmni ko'rganlar.
    returning_viewers = (
        ViewHistory.objects.values("user_id")
        .annotate(movie_total=Count("movie_id", distinct=True))
        .filter(movie_total__gte=2)
        .count()
    )

    return {
        "range_days": days,
        "totals": {
            "movies": Movie.objects.count(),
            "series": Series.objects.count(),
            "episodes": Episode.objects.count(),
            "users": User.objects.count(),
            "views": movie_totals["views"] or 0,
            "downloads": movie_totals["downloads"] or 0,
            "favorites": Favorite.objects.count(),
            "watchlist": Watchlist.objects.count(),
            "reviews": Review.objects.count(),
            "ratings": Rating.objects.count(),
            "avg_rating": round(movie_totals["avg_rating"] or 0, 2),
            "unique_viewers": unique_viewers,
            "returning_viewers": returning_viewers,
        },
        "period": {
            "new_users": _with_change(new_users_current, new_users_prev),
            "new_movies": _with_change(new_movies_current, new_movies_prev),
            "views": _with_change(views_current, views_prev),
        },
    }


def _with_change(current, previous):
    """``{"value": n, "change": foiz}`` -- oldingi davr 0 bo'lsa foiz hisoblanmaydi."""
    if previous:
        change = round((current - previous) / previous * 100, 1)
    else:
        change = None
    return {"value": current, "previous": previous, "change": change}
