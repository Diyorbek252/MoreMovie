"""AJAX endpointlar: watchlist, favorite va ko'rish progressi.

Barchasi POST + login talab qiladi. CSRF himoyasi Django middleware
tomonidan avtomatik qo'llanadi (JS `X-CSRFToken` header yuboradi).
"""

import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from shop.models import CinepointTransaction
from shop.services import has_earned, adjust_balance

from .models import Favorite, Movie, ViewHistory, Watchlist


def _parse_movie_id(request):
    """So'rov tanasidan movie id ni oladi (JSON yoki form-data)."""
    if request.content_type and "application/json" in request.content_type:
        try:
            payload = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return None
        return payload.get("movie")
    return request.POST.get("movie")


def _toggle(request, model):
    """Watchlist va Favorite uchun umumiy qo'shish/olib tashlash mantiqi."""
    movie_id = _parse_movie_id(request)
    if not movie_id:
        return JsonResponse({"error": "movie id ko'rsatilmagan"}, status=400)

    movie = get_object_or_404(Movie.objects.published(), pk=movie_id)

    entry, created = model.objects.get_or_create(user=request.user, movie=movie)
    if not created:
        entry.delete()

    return JsonResponse(
        {
            "added": created,
            "count": model.objects.filter(user=request.user).count(),
            "message": (
                "Ro'yxatga qo'shildi" if created else "Ro'yxatdan olib tashlandi"
            ),
        }
    )


@login_required
@require_POST
def toggle_watchlist(request):
    """POST /api/watchlist/toggle/  body: {"movie": <id>}"""
    return _toggle(request, Watchlist)


@login_required
@require_POST
def toggle_favorite(request):
    """POST /api/favorite/toggle/  body: {"movie": <id>}"""
    return _toggle(request, Favorite)


@login_required
@require_POST
def save_progress(request):
    """Player har 15 soniyada to'xtagan joyni yuboradi.

    POST /api/progress/  body: {"movie": <id>, "seconds": <int>, "finished": <bool>}
    """
    if request.content_type and "application/json" in request.content_type:
        try:
            payload = json.loads(request.body or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "noto'g'ri JSON"}, status=400)
    else:
        payload = request.POST

    movie_id = payload.get("movie")
    if not movie_id:
        return JsonResponse({"error": "movie id ko'rsatilmagan"}, status=400)

    movie = get_object_or_404(Movie.objects.published(), pk=movie_id)

    try:
        seconds = max(0, int(payload.get("seconds", 0)))
    except (TypeError, ValueError):
        seconds = 0

    finished = bool(payload.get("finished", False))

    history, _ = ViewHistory.objects.get_or_create(user=request.user, movie=movie)
    # Faqat hozir birinchi marta "tugatilgan" holatga o'tsa mukofot beramiz —
    # aks holda filmni qayta-qayta tomosha qilib cinepoint yig'ib bo'lmaydi.
    newly_finished = finished and not history.is_finished

    history.progress_seconds = seconds
    history.is_finished = finished
    history.save(update_fields=["progress_seconds", "is_finished"])

    if newly_finished and not has_earned(request.user, CinepointTransaction.Reason.MOVIE_WATCH, movie):
        adjust_balance(
            request.user,
            settings.CINEPOINT_MOVIE_REWARD,
            CinepointTransaction.Reason.MOVIE_WATCH,
            note=f"«{movie.title}» filmini ko'rish uchun",
            related=movie,
        )

    return JsonResponse({"saved": True, "seconds": seconds})
