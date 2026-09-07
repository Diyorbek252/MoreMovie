"""Barcha shablonlarga uzatiladigan umumiy kontekst."""

from django.conf import settings

from movies.models import Favorite, Genre, Watchlist
from siteconfig.models import NotificationRecipient


def site_globals(request):
    """Sayt brendi, navbar janrlari va foydalanuvchining to'plamlari.

    `user_watchlist_ids` / `user_favorite_ids` — kartalardagi yurak va bookmark
    tugmalarini to'g'ri holatda chizish uchun. Har karta uchun alohida so'rov
    qilmaslik maqsadida bir marta set sifatida olinadi.

    `unread_notifications_count` — navbar qo'ng'iroq ikonkasidagi belgi uchun.
    """
    context = {
        "SITE_NAME": settings.SITE_NAME,
        "SITE_TAGLINE": settings.SITE_TAGLINE,
        # Navbar dropdown'i uchun — filmi bor janrlar.
        "nav_genres": Genre.objects.all()[:12],
        "user_watchlist_ids": set(),
        "user_favorite_ids": set(),
        "unread_notifications_count": 0,
        # Navbar'dagi cinepoint chipi uchun.
        "cinepoint_balance": 0,
    }

    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        context["user_watchlist_ids"] = set(
            Watchlist.objects.filter(user=user).values_list("movie_id", flat=True)
        )
        context["user_favorite_ids"] = set(
            Favorite.objects.filter(user=user).values_list("movie_id", flat=True)
        )
        context["unread_notifications_count"] = NotificationRecipient.objects.filter(
            user=user, is_read=False
        ).count()
        # Profile signal orqali har bir User uchun kafolatlangan.
        context["cinepoint_balance"] = user.profile.balance

    return context
