"""AJAX endpointlar: reyting berish va sharh yuborish."""

import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from movies.models import Movie

from .models import Rating, Review


def _payload(request):
    if request.content_type and "application/json" in request.content_type:
        try:
            return json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return {}
    return request.POST


@login_required
@require_POST
def rate_movie(request):
    """POST /api/rate/  body: {"movie": <id>, "score": 1..5}

    Bitta foydalanuvchi bitta filmga faqat bitta baho beradi — qayta
    yuborilsa mavjud baho yangilanadi (UniqueConstraint tufayli).
    """
    data = _payload(request)
    movie_id = data.get("movie")

    try:
        score = int(data.get("score", 0))
    except (TypeError, ValueError):
        score = 0

    if not movie_id or not 1 <= score <= 5:
        return JsonResponse({"error": "Baho 1 dan 5 gacha bo'lishi kerak."}, status=400)

    movie = get_object_or_404(Movie.objects.published(), pk=movie_id)

    rating, created = Rating.objects.update_or_create(
        user=request.user, movie=movie, defaults={"score": score}
    )
    # Rating.save() Movie.recalculate_rating() ni chaqirgan — yangi qiymatni o'qiymiz.
    # Faqat moderatsiyadan o'tgan sharh egalarining bahosi hisoblanadi, shuning
    # uchun bu baho o'rtachaga hali kirmagan bo'lishi mumkin (sharh tasdiqlanmagan).
    movie.refresh_from_db(fields=["avg_rating", "rating_count"])
    display = movie.user_rating_display

    return JsonResponse(
        {
            "score": rating.score,
            "average": float(movie.avg_rating),
            "count": movie.rating_count,
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
    """POST /api/review/  body: {"movie": <id>, "comment": "..."}

    Sharh moderatsiyaga tushadi — tasdiqlangunicha saytda ko'rinmaydi.
    """
    data = _payload(request)
    movie_id = data.get("movie")
    comment = (data.get("comment") or "").strip()

    if not movie_id:
        return JsonResponse({"error": "movie id ko'rsatilmagan"}, status=400)

    if len(comment) < 10:
        return JsonResponse(
            {"error": "Sharh kamida 10 ta belgidan iborat bo'lishi kerak."}, status=400
        )

    if len(comment) > 2000:
        return JsonResponse({"error": "Sharh 2000 belgidan oshmasligi kerak."}, status=400)

    movie = get_object_or_404(Movie.objects.published(), pk=movie_id)

    # Tahrirlangan sharh qaytadan moderatsiyaga tushadi.
    review, created = Review.objects.update_or_create(
        user=request.user,
        movie=movie,
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
