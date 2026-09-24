"""DRF API — autentifikatsiya, profil, watchlist/favorites/tarix ro'yxatlari.

Sessiya cookie orqali ishlaydi (frontend va backend bitta domenda) — token/
JWT yo'q. `POST /auth/login/` va `/auth/register/` muvaffaqiyatli bo'lsa
Django sessiyasini o'rnatadi, xuddi eski `LoginView`/`RegisterView` kabi.
"""

from django.contrib.auth import login, logout
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from movies.models import Favorite, Watchlist
from movies.serializers import MovieCardSerializer

from .serializers import (
    LoginSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    UserSerializer,
)


class CsrfView(APIView):
    """`GET /api/v1/auth/csrf/` — Next.js uchun `csrftoken` cookie o'rnatadi.

    Session-based auth'da yozuvchi so'rovlardan oldin frontend shu
    endpoint'ni bir marta chaqirib CSRF cookie oladi, so'ng har POST/PATCH
    da uni `X-CSRFToken` header sifatida qaytaradi (Django standart sxemasi).
    """

    permission_classes = [permissions.AllowAny]

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        return Response({"csrftoken": get_token(request)})


class RegisterView(APIView):
    """`POST /api/v1/auth/register/` — muvaffaqiyatli bo'lsa darhol kirgizadi."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Backend'ni aniq ko'rsatamiz — ikkita AUTHENTICATION_BACKENDS
        # sozlangani uchun shart (users/views.py::RegisterView bilan bir xil).
        login(request, user, backend="users.backends.EmailOrUsernameBackend")
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """`POST /api/v1/auth/login/`  body: {"username": .., "password": .., "remember_me": bool}"""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, request=request)
        serializer.is_valid(raise_exception=True)
        user = serializer.user
        login(request, user, backend=user.backend)
        if not serializer.remember_me:
            request.session.set_expiry(0)
        return Response(UserSerializer(user).data)


class LogoutView(APIView):
    """`POST /api/v1/auth/logout/`"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"ok": True})


class MeView(APIView):
    """`GET /api/v1/auth/me/` — joriy foydalanuvchi (anonim bo'lsa 401)."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        if not request.user.is_authenticated:
            return Response({"detail": "Tizimga kirilmagan."}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(UserSerializer(request.user).data)


class ProfileUpdateView(APIView):
    """`PATCH /api/v1/me/profile/` — `UserForm` + `ProfileForm` birga."""

    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        serializer = ProfileUpdateSerializer(
            data=request.data, instance=request.user, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)


class DismissContinueWatchingView(APIView):
    """`POST /api/v1/me/continue-watching/dismiss/` — `users/api.py` DRF ekvivalenti."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        profile = request.user.profile
        if profile.show_continue_watching:
            profile.show_continue_watching = False
            profile.save(update_fields=["show_continue_watching"])
        return Response(
            {
                "message": (
                    "«Davom ettirish» bo'limi yashirildi. Uni profil "
                    "sozlamalaridan istalgan payt qaytarib yoqishingiz mumkin."
                ),
            }
        )


class _MovieRelationListView(generics.ListAPIView):
    """Watchlist/Favorites uchun umumiy — ikkalasi ham bir xil shaklda
    (foydalanuvchining film ro'yxati) qaytadi."""

    serializer_class = MovieCardSerializer
    permission_classes = [permissions.IsAuthenticated]
    relation_model = None

    def get_queryset(self):
        entries = (
            self.relation_model.objects.filter(user=self.request.user)
            .select_related("movie", "movie__language")
            .prefetch_related("movie__genres", "movie__directors", "movie__countries")
        )
        # `MovieCardSerializer` Movie obyektini kutadi — bog'lovchi
        # jadvaldan (Watchlist/Favorite) filmlarni ajratib olamiz, tartib
        # `-added_at` bo'yicha saqlanadi (model Meta.ordering).
        return [entry.movie for entry in entries]


class WatchlistListView(_MovieRelationListView):
    relation_model = Watchlist


class FavoritesListView(_MovieRelationListView):
    relation_model = Favorite
