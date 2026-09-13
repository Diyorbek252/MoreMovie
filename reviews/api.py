"""AJAX endpointlar: reyting berish va sharh yuborish.

Film HAM serial baholanishi/sharh qoldirilishi mumkin — so'rov tanasida
`movie` yoki `series` kalitlaridan ANIQ BITTASI keladi (qarang:
reviews.models — "target" naqshi).
"""

import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from movies.models import Movie
from series.models import Series

from .models import Rating, Review


def _payload(request):
    if request.content_type and "application/json" in request.content_type:
        try:
            return json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return {}
    return request.POST


def _resolve_target(data):
    """So'rov tanasidan film yoki serialni topadi.

    Ikkalasi ham berilmasa yoki ikkalasi ham berilsa — xato. Muvaffaqiyatli
    bo'lsa ``(target, field_name)`` qaytaradi, ``field_name`` esa
    ``Rating``/``Review`` ga qaysi maydon orqali (``"movie"`` yoki
    ``"series"``) bog'lashni bildiradi.
    """
    movie_id = data.get("movie")
    series_id = data.get("series")

    if movie_id and not series_id:
        return get_object_or_404(Movie.objects.published(), pk=movie_id), "movie"
    if series_id and not movie_id:
        return get_object_or_404(Series.objects.published(), pk=series_id), "series"
    return None, None


@login_required
@require_POST
def rate_movie(request):
    """POST /api/rate/  body: {"movie": <id>, "score": 1..5} yoki {"series": <id>, ...}

    Bitta foydalanuvchi bitta film/serialga faqat bitta baho beradi —
    qayta yuborilsa mavjud baho yangilanadi (UniqueConstraint tufayli).
    """
    data = _payload(request)

    try:
        score = int(data.get("score", 0))
    except (TypeError, ValueError):
        score = 0

    target, field_name = _resolve_target(data)

    if not target or not 1 <= score <= 5:
        return JsonResponse({"error": "Baho 1 dan 5 gacha bo'lishi kerak."}, status=400)

    rating, created = Rating.objects.update_or_create(
        user=request.user, **{field_name: target}, defaults={"score": score}
    )
    # Rating.save() target.recalculate_rating() ni chaqirgan — yangi qiymatni o'qiymiz.
    # Faqat moderatsiyadan o'tgan sharh egalarining bahosi hisoblanadi, shuning
    # uchun bu baho o'rtachaga hali kirmagan bo'lishi mumkin (sharh tasdiqlanmagan).
    target.refresh_from_db(fields=["avg_rating", "rating_count"])
    display = target.user_rating_display

    return JsonResponse(
        {
            "score": rating.score,
            "average": float(target.avg_rating),
            "count": target.rating_count,
            # Sahifada server chizgan qiymat bilan bir xil ko'rinishi uchun
            # matn sifatida ("4.0", "4" emas). Sayt o'rtachasi hali yo'q
            # bo'lsa (masalan, sharh hali tasdiqlanmagan) — null.
            "user_rating": f"{display:.1f}" if display is not None else None,
            "message": "Bahoyingiz qabul qilindi" if created else "Bahoyingiz yangilandi",
        }
    )


@login_required
@require_POST
def submit_review(request):
    """POST /api/review/  body: {"movie": <id>, "comment": "..."} yoki {"series": <id>, ...}

    Sharh moderatsiyaga tushadi — tasdiqlangunicha saytda ko'rinmaydi.
    """
    data = _payload(request)
    comment = (data.get("comment") or "").strip()

    target, field_name = _resolve_target(data)

    if not target:
        return JsonResponse({"error": "film yoki serial ko'rsatilmagan"}, status=400)

    if len(comment) < 10:
        return JsonResponse(
            {"error": "Sharh kamida 10 ta belgidan iborat bo'lishi kerak."}, status=400
        )

    if len(comment) > 2000:
        return JsonResponse({"error": "Sharh 2000 belgidan oshmasligi kerak."}, status=400)

    # Tahrirlangan sharh qaytadan moderatsiyaga tushadi.
    review, created = Review.objects.update_or_create(
        user=request.user,
        **{field_name: target},
        defaults={"comment": comment, "status": Review.Status.PENDING},
    )

    return JsonResponse(
        {
            "created": created,
            "status": review.status,
            "message": (
                "Sharhingiz yuborildi va moderatsiyadan keyin chop etiladi."
                if created
                else "Sharhingiz yangilandi va qayta moderatsiyaga yuborildi."
            ),
        }
    )
