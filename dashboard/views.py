"""Custom boshqaruv paneli — faqat xodimlar (is_staff) uchun.

Django admin'dan farqi: sayt bilan bir xil dizayn tizimida ishlaydi va
kundalik operatsiyalar (chop etish, moderatsiya, bloklash) uchun
soddalashtirilgan.
"""

import json
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Avg, Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    TemplateView,
    UpdateView,
)

from core.models import ContactMessage
from movies.models import Favorite, Genre, Movie, ViewHistory, Watchlist
from reviews.models import Review

from .forms import GenreForm, MovieForm

User = get_user_model()


class StaffRequiredMixin(UserPassesTestMixin):
    """Dashboard'ning barcha sahifalari uchun majburiy tekshiruv.

    `raise_exception = True` — tizimga kirmagan foydalanuvchi login sahifasiga
    yo'naltiriladi, kirgan lekin xodim bo'lmagani esa 403 oladi.
    """

    raise_exception = True

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.is_staff and not user.is_blocked

    def get_context_data(self, **kwargs):
        """Yon menyudagi "kutilmoqda" hisoblagichlari — barcha sahifalarda ko'rinadi."""
        context = super().get_context_data(**kwargs)
        context["nav_counts"] = {
            "reviews_pending": Review.objects.filter(status=Review.Status.PENDING).count(),
            "messages_unread": ContactMessage.objects.filter(is_read=False).count(),
        }
        return context


class DashboardIndexView(StaffRequiredMixin, TemplateView):
    """Bosh panel — statistika kartalari va grafik."""

    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        movie_stats = Movie.objects.aggregate(
            total=Count("id"),
            published=Count("id", filter=Q(is_published=True)),
            views=Sum("views_count"),
            avg=Avg("avg_rating", filter=Q(rating_count__gt=0)),
        )

        context["stats"] = {
            "movies_total": movie_stats["total"] or 0,
            "movies_published": movie_stats["published"] or 0,
            "movies_draft": (movie_stats["total"] or 0) - (movie_stats["published"] or 0),
            "views_total": movie_stats["views"] or 0,
            "avg_rating": round(movie_stats["avg"] or 0, 2),
            "users_total": User.objects.count(),
            "users_blocked": User.objects.filter(is_blocked=True).count(),
            "favorites_total": Favorite.objects.count(),
            "watchlist_total": Watchlist.objects.count(),
            "reviews_pending": Review.objects.filter(status=Review.Status.PENDING).count(),
            "messages_unread": ContactMessage.objects.filter(is_read=False).count(),
        }

        # Eng mashhur 10 film.
        context["popular_movies"] = (
            Movie.objects.published()
            .annotate(fav_count=Count("favorite_entries", distinct=True))
            .order_by("-views_count")[:10]
        )

        # Moderatsiya kutayotgan sharhlar.
        context["pending_reviews"] = (
            Review.objects.filter(status=Review.Status.PENDING)
            .select_related("user", "movie")
            .order_by("-created_at")[:8]
        )

        # Oxirgi 14 kunlik ko'rishlar — inline SVG grafik uchun.
        context["chart_data"] = json.dumps(self._daily_views(days=14))

        context["recent_users"] = User.objects.order_by("-date_joined")[:8]

        return context

    def _daily_views(self, days=14):
        """Kunlik ko'rishlar sonini [{"label": "12/03", "value": n}, ...] shaklida."""
        today = timezone.localdate()
        start = today - timedelta(days=days - 1)

        # Bitta so'rov bilan kunlar bo'yicha guruhlaymiz.
        rows = (
            ViewHistory.objects.filter(watched_at__date__gte=start)
            .values("watched_at__date")
            .annotate(total=Count("id"))
        )
        counts = {row["watched_at__date"]: row["total"] for row in rows}

        return [
            {
                "label": (start + timedelta(days=i)).strftime("%d/%m"),
                "value": counts.get(start + timedelta(days=i), 0),
            }
            for i in range(days)
        ]


# ---------------------------------------------------------------------------
# Filmlar
# ---------------------------------------------------------------------------


class MovieManageListView(StaffRequiredMixin, ListView):
    """Filmlar jadvali — qidiruv va holat filtri bilan."""

    model = Movie
    template_name = "dashboard/movie_list.html"
    context_object_name = "movies"
    paginate_by = 20

    def get_queryset(self):
        queryset = Movie.objects.select_related("country", "language", "director")

        if query := self.request.GET.get("q", "").strip():
            queryset = queryset.filter(
                Q(title__icontains=query) | Q(director__full_name__icontains=query)
            )

        status = self.request.GET.get("status")
        if status == "published":
            queryset = queryset.filter(is_published=True)
        elif status == "draft":
            queryset = queryset.filter(is_published=False)
        elif status == "featured":
            queryset = queryset.filter(is_featured=True)

        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_q"] = self.request.GET.get("q", "")
        context["current_status"] = self.request.GET.get("status", "")
        params = self.request.GET.copy()
        params.pop("page", None)
        context["querystring"] = params.urlencode()
        return context


class MovieCreateView(StaffRequiredMixin, CreateView):
    model = Movie
    form_class = MovieForm
    template_name = "dashboard/movie_form.html"
    success_url = reverse_lazy("dashboard:movie_list")

    def form_valid(self, form):
        messages.success(self.request, f"«{form.instance.title}» qo'shildi.")
        return super().form_valid(form)


class MovieUpdateView(StaffRequiredMixin, UpdateView):
    model = Movie
    form_class = MovieForm
    template_name = "dashboard/movie_form.html"
    success_url = reverse_lazy("dashboard:movie_list")

    def form_valid(self, form):
        messages.success(self.request, f"«{form.instance.title}» yangilandi.")
        return super().form_valid(form)


class MovieDeleteView(StaffRequiredMixin, DeleteView):
    model = Movie
    template_name = "dashboard/movie_confirm_delete.html"
    success_url = reverse_lazy("dashboard:movie_list")

    def form_valid(self, form):
        messages.success(self.request, f"«{self.object.title}» o'chirildi.")
        return super().form_valid(form)


# ---------------------------------------------------------------------------
# Janrlar
# ---------------------------------------------------------------------------


class GenreManageView(StaffRequiredMixin, ListView):
    """Janrlar ro'yxati + qo'shish formasi bir sahifada."""

    model = Genre
    template_name = "dashboard/genre_list.html"
    context_object_name = "genres"

    def get_queryset(self):
        return Genre.objects.annotate(movie_total=Count("movies")).order_by("order", "name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = GenreForm()
        return context

    def post(self, request, *args, **kwargs):
        form = GenreForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"«{form.instance.name}» janri qo'shildi.")
        else:
            messages.error(request, "Janr qo'shilmadi — nom takrorlanmasligi kerak.")
        return redirect("dashboard:genre_list")


class GenreUpdateView(StaffRequiredMixin, UpdateView):
    model = Genre
    form_class = GenreForm
    template_name = "dashboard/genre_form.html"
    success_url = reverse_lazy("dashboard:genre_list")

    def form_valid(self, form):
        messages.success(self.request, "Janr yangilandi.")
        return super().form_valid(form)


class GenreDeleteView(StaffRequiredMixin, DeleteView):
    model = Genre
    template_name = "dashboard/genre_confirm_delete.html"
    success_url = reverse_lazy("dashboard:genre_list")

    def form_valid(self, form):
        messages.success(self.request, f"«{self.object.name}» janri o'chirildi.")
        return super().form_valid(form)


# ---------------------------------------------------------------------------
# Foydalanuvchilar
# ---------------------------------------------------------------------------


class UserManageListView(StaffRequiredMixin, ListView):
    model = User
    template_name = "dashboard/user_list.html"
    context_object_name = "users_list"
    paginate_by = 25

    def get_queryset(self):
        queryset = User.objects.all()

        if query := self.request.GET.get("q", "").strip():
            queryset = queryset.filter(
                Q(username__icontains=query) | Q(email__icontains=query)
            )

        status = self.request.GET.get("status")
        if status == "blocked":
            queryset = queryset.filter(is_blocked=True)
        elif status == "staff":
            queryset = queryset.filter(is_staff=True)

        return queryset.annotate(
            fav_count=Count("favorite_items", distinct=True),
            review_count=Count("reviews", distinct=True),
        ).order_by("-date_joined")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_q"] = self.request.GET.get("q", "")
        context["current_status"] = self.request.GET.get("status", "")
        params = self.request.GET.copy()
        params.pop("page", None)
        context["querystring"] = params.urlencode()
        return context


# ---------------------------------------------------------------------------
# Sharhlar
# ---------------------------------------------------------------------------


class ReviewManageListView(StaffRequiredMixin, ListView):
    model = Review
    template_name = "dashboard/review_list.html"
    context_object_name = "reviews"
    paginate_by = 25

    def get_queryset(self):
        queryset = Review.objects.select_related("user", "movie")
        status = self.request.GET.get("status", "pending")
        if status in dict(Review.Status.choices):
            queryset = queryset.filter(status=status)
        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_status"] = self.request.GET.get("status", "pending")
        context["status_choices"] = Review.Status.choices
        context["counts"] = {
            "pending": Review.objects.filter(status=Review.Status.PENDING).count(),
            "approved": Review.objects.filter(status=Review.Status.APPROVED).count(),
            "rejected": Review.objects.filter(status=Review.Status.REJECTED).count(),
        }
        params = self.request.GET.copy()
        params.pop("page", None)
        context["querystring"] = params.urlencode()
        return context


class MessageListView(StaffRequiredMixin, ListView):
    """Contact formasidan kelgan murojaatlar."""

    model = ContactMessage
    template_name = "dashboard/message_list.html"
    context_object_name = "contact_messages"
    paginate_by = 25

    def get_queryset(self):
        return ContactMessage.objects.all()


# ---------------------------------------------------------------------------
# AJAX harakatlar
# ---------------------------------------------------------------------------


def _staff_check(request):
    """AJAX endpointlar uchun ruxsat tekshiruvi."""
    user = request.user
    return user.is_authenticated and user.is_staff and not user.is_blocked


@require_POST
def toggle_publish(request, pk):
    """Filmni chop etish / yashirish (AJAX)."""
    if not _staff_check(request):
        return JsonResponse({"error": "Ruxsat yo'q"}, status=403)

    movie = get_object_or_404(Movie, pk=pk)
    movie.is_published = not movie.is_published
    movie.save(update_fields=["is_published", "updated_at"])

    return JsonResponse(
        {
            "published": movie.is_published,
            "message": f"«{movie.title}» {'chop etildi' if movie.is_published else 'yashirildi'}",
        }
    )


@require_POST
def toggle_featured(request, pk):
    """Filmni "tanlangan" qilish / bekor qilish (AJAX)."""
    if not _staff_check(request):
        return JsonResponse({"error": "Ruxsat yo'q"}, status=403)

    movie = get_object_or_404(Movie, pk=pk)
    movie.is_featured = not movie.is_featured
    movie.save(update_fields=["is_featured", "updated_at"])

    return JsonResponse({"featured": movie.is_featured})


@require_POST
def toggle_block(request, pk):
    """Foydalanuvchini bloklash / blokdan chiqarish (AJAX)."""
    if not _staff_check(request):
        return JsonResponse({"error": "Ruxsat yo'q"}, status=403)

    target = get_object_or_404(User, pk=pk)

    # O'zini yoki superuser'ni bloklashga yo'l qo'ymaymiz.
    if target == request.user:
        return JsonResponse({"error": "O'zingizni bloklay olmaysiz."}, status=400)
    if target.is_superuser:
        return JsonResponse({"error": "Superuser'ni bloklab bo'lmaydi."}, status=400)

    target.is_blocked = not target.is_blocked
    target.save(update_fields=["is_blocked"])

    return JsonResponse(
        {
            "blocked": target.is_blocked,
            "message": f"{target.username} {'bloklandi' if target.is_blocked else 'blokdan chiqarildi'}",
        }
    )


@require_POST
def moderate_review(request, pk, action):
    """Sharhni tasdiqlash / rad etish / o'chirish (AJAX)."""
    if not _staff_check(request):
        return JsonResponse({"error": "Ruxsat yo'q"}, status=403)

    review = get_object_or_404(Review, pk=pk)

    if action == "approve":
        review.status = Review.Status.APPROVED
        review.save(update_fields=["status", "updated_at"])
        return JsonResponse({"status": "approved", "message": "Sharh tasdiqlandi"})

    if action == "reject":
        review.status = Review.Status.REJECTED
        review.save(update_fields=["status", "updated_at"])
        return JsonResponse({"status": "rejected", "message": "Sharh rad etildi"})

    if action == "delete":
        review.delete()
        return JsonResponse({"status": "deleted", "message": "Sharh o'chirildi"})

    return JsonResponse({"error": "Noma'lum amal"}, status=400)
