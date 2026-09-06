"""Custom boshqaruv paneli — faqat xodimlar (is_staff) uchun.

Django admin'dan farqi: sayt bilan bir xil dizayn tizimida ishlaydi va
kundalik operatsiyalar (chop etish, moderatsiya, bloklash) uchun
soddalashtirilgan.
"""

import json

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from core.models import ContactMessage
from movies.models import Category, Favorite, Genre, Movie, Watchlist
from reviews.models import Review
from series.models import Episode, Season, Series
from siteconfig.models import Banner, HomepageSection, Notification, SiteSettings

from . import analytics
from .forms import (
    BannerForm,
    CategoryForm,
    EpisodeForm,
    GenreForm,
    HomepageSectionForm,
    MovieForm,
    NotificationForm,
    SeasonForm,
    SeriesForm,
    SiteSettingsForm,
)
from .mixins import DashboardPermissionMixin, StaffRequiredMixin, dashboard_perm_required

User = get_user_model()

# Eslatma: `StaffRequiredMixin` endi `.mixins` dan import qilinadi (bu yerda
# import qilib qo'yilishi eski kodni buzmasligi uchun). Yangi view'lar
# `DashboardPermissionMixin` dan to'g'ridan-to'g'ri, `required_perms` bilan
# meros olishi kerak — pastdagi misollarga qarang.


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
            "series_total": Series.objects.count(),
            "episodes_total": Episode.objects.count(),
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
        # `analytics.daily_views()` bilan bir xil naqsh -- Blok F da shu
        # yerdan ko'chirilib, umumiy modulga o'tkazilgan (Analitika sahifasi
        # ham shundan foydalanadi, mantiq ikki joyda takrorlanmaydi).
        context["chart_data"] = json.dumps(analytics.daily_views(days=14))

        context["recent_users"] = User.objects.order_by("-date_joined")[:8]

        return context


class AnalyticsView(DashboardPermissionMixin, TemplateView):
    """Analitika sahifasi -- sof so'rov funksiyalari (`dashboard/analytics.py`)
    ustiga qurilgan yupqa view. Barcha og'ir hisob-kitob o'sha modulda."""

    required_perms = ["dashboard.view_analytics"]
    template_name = "dashboard/analytics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        range_key, range_label, days = analytics.resolve_range(
            self.request.GET.get("range", analytics.DEFAULT_RANGE)
        )

        context["range_key"] = range_key
        context["range_label"] = range_label
        context["range_choices"] = analytics.DATE_RANGES

        context["summary"] = analytics.engagement_summary(days=days)

        context["views_chart"] = json.dumps(analytics.daily_views(days=days))
        context["user_growth_chart"] = json.dumps(analytics.user_growth(days=days))
        context["content_growth_chart"] = json.dumps(analytics.content_growth(days=days))

        context["top_movies_views"] = analytics.top_movies(10, "views")
        context["top_movies_downloads"] = analytics.top_movies(10, "downloads")
        context["top_movies_rating"] = analytics.top_movies(10, "rating")
        context["top_series"] = analytics.top_series(10)

        context["genre_share"] = analytics.genre_share(8)
        context["rating_distribution"] = analytics.rating_distribution()

        return context


# ---------------------------------------------------------------------------
# Filmlar
# ---------------------------------------------------------------------------


class MovieManageListView(DashboardPermissionMixin, ListView):
    """Filmlar jadvali — qidiruv va holat filtri bilan."""

    required_perms = ["movies.view_movie"]
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


class MovieCreateView(DashboardPermissionMixin, CreateView):
    required_perms = ["movies.add_movie"]
    model = Movie
    form_class = MovieForm
    template_name = "dashboard/movie_form.html"
    success_url = reverse_lazy("dashboard:movie_list")

    def form_valid(self, form):
        messages.success(self.request, f"«{form.instance.title}» qo'shildi.")
        return super().form_valid(form)


class MovieUpdateView(DashboardPermissionMixin, UpdateView):
    required_perms = ["movies.change_movie"]
    model = Movie
    form_class = MovieForm
    template_name = "dashboard/movie_form.html"
    success_url = reverse_lazy("dashboard:movie_list")

    def form_valid(self, form):
        messages.success(self.request, f"«{form.instance.title}» yangilandi.")
        return super().form_valid(form)


class MovieDeleteView(DashboardPermissionMixin, DeleteView):
    required_perms = ["movies.delete_movie"]
    model = Movie
    template_name = "dashboard/movie_confirm_delete.html"
    success_url = reverse_lazy("dashboard:movie_list")

    def form_valid(self, form):
        messages.success(self.request, f"«{self.object.title}» o'chirildi.")
        return super().form_valid(form)


# ---------------------------------------------------------------------------
# Janrlar
# ---------------------------------------------------------------------------


class GenreManageView(DashboardPermissionMixin, ListView):
    """Janrlar ro'yxati + qo'shish formasi bir sahifada."""

    required_perms = ["movies.view_genre"]
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


class GenreUpdateView(DashboardPermissionMixin, UpdateView):
    required_perms = ["movies.change_genre"]
    model = Genre
    form_class = GenreForm
    template_name = "dashboard/genre_form.html"
    success_url = reverse_lazy("dashboard:genre_list")

    def form_valid(self, form):
        messages.success(self.request, "Janr yangilandi.")
        return super().form_valid(form)


class GenreDeleteView(DashboardPermissionMixin, DeleteView):
    required_perms = ["movies.delete_genre"]
    model = Genre
    template_name = "dashboard/genre_confirm_delete.html"
    success_url = reverse_lazy("dashboard:genre_list")

    def form_valid(self, form):
        messages.success(self.request, f"«{self.object.name}» janri o'chirildi.")
        return super().form_valid(form)


# ---------------------------------------------------------------------------
# Kategoriyalar
# ---------------------------------------------------------------------------


class CategoryManageView(DashboardPermissionMixin, ListView):
    """Kategoriyalar ro'yxati + qo'shish formasi bir sahifada (Genre bilan bir xil naqsh)."""

    required_perms = ["movies.view_category"]
    model = Category
    template_name = "dashboard/category_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        return Category.objects.annotate(movie_total=Count("movies")).order_by("order", "name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = CategoryForm()
        return context

    def post(self, request, *args, **kwargs):
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, f"«{form.instance.name}» kategoriyasi qo'shildi.")
        else:
            messages.error(request, "Kategoriya qo'shilmadi — nom takrorlanmasligi kerak.")
        return redirect("dashboard:category_list")


class CategoryUpdateView(DashboardPermissionMixin, UpdateView):
    required_perms = ["movies.change_category"]
    model = Category
    form_class = CategoryForm
    template_name = "dashboard/category_form.html"
    success_url = reverse_lazy("dashboard:category_list")

    def form_valid(self, form):
        messages.success(self.request, "Kategoriya yangilandi.")
        return super().form_valid(form)


class CategoryDeleteView(DashboardPermissionMixin, DeleteView):
    required_perms = ["movies.delete_category"]
    model = Category
    template_name = "dashboard/category_confirm_delete.html"
    success_url = reverse_lazy("dashboard:category_list")

    def form_valid(self, form):
        messages.success(self.request, f"«{self.object.name}» kategoriyasi o'chirildi.")
        return super().form_valid(form)


# ---------------------------------------------------------------------------
# Foydalanuvchilar
# ---------------------------------------------------------------------------


class UserManageListView(DashboardPermissionMixin, ListView):
    required_perms = ["users.view_user"]
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


class ReviewManageListView(DashboardPermissionMixin, ListView):
    required_perms = ["reviews.view_review"]
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

        # Bitta so'rov bilan barcha holatlar bo'yicha son — status qo'shilsa
        # ham (masalan kelajakda) kodni o'zgartirish shart emas.
        rows = Review.objects.values("status").annotate(total=Count("id"))
        counts = {value: 0 for value, _ in Review.Status.choices}
        counts.update({row["status"]: row["total"] for row in rows})
        context["counts"] = counts

        params = self.request.GET.copy()
        params.pop("page", None)
        context["querystring"] = params.urlencode()
        return context


class MessageListView(DashboardPermissionMixin, ListView):
    """Contact formasidan kelgan murojaatlar."""

    required_perms = ["core.view_contactmessage"]
    model = ContactMessage
    template_name = "dashboard/message_list.html"
    context_object_name = "contact_messages"
    paginate_by = 25

    def get_queryset(self):
        return ContactMessage.objects.all()

# ---------------------------------------------------------------------------
# Seriallar / fasllar / epizodlar
# ---------------------------------------------------------------------------


class SeriesManageListView(DashboardPermissionMixin, ListView):
    """Seriallar jadvali — Movie ro'yxati bilan bir xil naqsh."""

    required_perms = ["series.view_series"]
    model = Series
    template_name = "dashboard/series_list.html"
    context_object_name = "series_list"
    paginate_by = 20

    def get_queryset(self):
        queryset = Series.objects.select_related("country", "language", "director")

        if query := self.request.GET.get("q", "").strip():
            queryset = queryset.filter(
                Q(title__icontains=query) | Q(director__full_name__icontains=query)
            )

        status = self.request.GET.get("status")
        if status == "published":
            queryset = queryset.filter(is_published=True)
        elif status == "draft":
            queryset = queryset.filter(is_published=False)

        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_q"] = self.request.GET.get("q", "")
        context["current_status"] = self.request.GET.get("status", "")
        params = self.request.GET.copy()
        params.pop("page", None)
        context["querystring"] = params.urlencode()
        return context


class SeriesCreateView(DashboardPermissionMixin, CreateView):
    required_perms = ["series.add_series"]
    model = Series
    form_class = SeriesForm
    template_name = "dashboard/series_form.html"
    success_url = reverse_lazy("dashboard:series_list")

    def form_valid(self, form):
        messages.success(self.request, f"«{form.instance.title}» qo'shildi.")
        return super().form_valid(form)


class SeriesUpdateView(DashboardPermissionMixin, UpdateView):
    required_perms = ["series.change_series"]
    model = Series
    form_class = SeriesForm
    template_name = "dashboard/series_form.html"
    success_url = reverse_lazy("dashboard:series_list")

    def form_valid(self, form):
        messages.success(self.request, f"«{form.instance.title}» yangilandi.")
        return super().form_valid(form)


class SeriesDeleteView(DashboardPermissionMixin, DeleteView):
    required_perms = ["series.delete_series"]
    model = Series
    template_name = "dashboard/series_confirm_delete.html"
    success_url = reverse_lazy("dashboard:series_list")

    def form_valid(self, form):
        messages.success(self.request, f"«{self.object.title}» o'chirildi.")
        return super().form_valid(form)


class SeasonListView(DashboardPermissionMixin, ListView):
    """Bitta serialning fasllari ro'yxati — /dashboard/series/<pk>/seasons/."""

    required_perms = ["series.view_season"]
    template_name = "dashboard/season_list.html"
    context_object_name = "seasons"

    def get_queryset(self):
        self.series = get_object_or_404(Series, pk=self.kwargs["series_pk"])
        return Season.objects.filter(series=self.series).annotate(
            episode_total=Count("episodes")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["series"] = self.series
        return context


class SeasonCreateView(DashboardPermissionMixin, CreateView):
    """Fasl qo'shish — series_pk URL orqali keladi, forma o'zida ko'rsatilmaydi."""

    required_perms = ["series.add_season"]
    model = Season
    form_class = SeasonForm
    template_name = "dashboard/season_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.series = get_object_or_404(Series, pk=kwargs["series_pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.series = self.series
        messages.success(self.request, f"{form.instance.number}-fasl qo'shildi.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["series"] = self.series
        return context

    def get_success_url(self):
        return reverse_lazy("dashboard:season_list", kwargs={"series_pk": self.series.pk})


class SeasonUpdateView(DashboardPermissionMixin, UpdateView):
    required_perms = ["series.change_season"]
    model = Season
    form_class = SeasonForm
    template_name = "dashboard/season_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["series"] = self.object.series
        return context

    def form_valid(self, form):
        messages.success(self.request, f"{form.instance.number}-fasl yangilandi.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("dashboard:season_list", kwargs={"series_pk": self.object.series.pk})


class SeasonDeleteView(DashboardPermissionMixin, DeleteView):
    required_perms = ["series.delete_season"]
    model = Season
    template_name = "dashboard/season_confirm_delete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["series"] = self.object.series
        return context

    def form_valid(self, form):
        series_pk = self.object.series.pk
        messages.success(self.request, f"{self.object.number}-fasl o'chirildi.")
        self.success_url = reverse_lazy("dashboard:season_list", kwargs={"series_pk": series_pk})
        return super().form_valid(form)


class EpisodeListView(DashboardPermissionMixin, ListView):
    """Bitta faslning epizodlari — /dashboard/seasons/<pk>/episodes/."""

    required_perms = ["series.view_episode"]
    template_name = "dashboard/episode_list.html"
    context_object_name = "episodes"

    def get_queryset(self):
        self.season = get_object_or_404(
            Season.objects.select_related("series"), pk=self.kwargs["season_pk"]
        )
        return Episode.objects.filter(season=self.season).order_by("episode_number")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["season"] = self.season
        return context


class EpisodeCreateView(DashboardPermissionMixin, CreateView):
    required_perms = ["series.add_episode"]
    model = Episode
    form_class = EpisodeForm
    template_name = "dashboard/episode_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.season = get_object_or_404(
            Season.objects.select_related("series"), pk=kwargs["season_pk"]
        )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.season = self.season
        messages.success(self.request, f"«{form.instance.title}» epizodi qo'shildi.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["season"] = self.season
        return context

    def get_success_url(self):
        return reverse_lazy("dashboard:episode_list", kwargs={"season_pk": self.season.pk})


class EpisodeUpdateView(DashboardPermissionMixin, UpdateView):
    required_perms = ["series.change_episode"]
    model = Episode
    form_class = EpisodeForm
    template_name = "dashboard/episode_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["season"] = self.object.season
        return context

    def form_valid(self, form):
        messages.success(self.request, f"«{form.instance.title}» epizodi yangilandi.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("dashboard:episode_list", kwargs={"season_pk": self.object.season.pk})


class EpisodeDeleteView(DashboardPermissionMixin, DeleteView):
    required_perms = ["series.delete_episode"]
    model = Episode
    template_name = "dashboard/episode_confirm_delete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["season"] = self.object.season
        return context

    def form_valid(self, form):
        season_pk = self.object.season.pk
        messages.success(self.request, f"«{self.object.title}» epizodi o'chirildi.")
        self.success_url = reverse_lazy("dashboard:episode_list", kwargs={"season_pk": season_pk})
        return super().form_valid(form)


# ---------------------------------------------------------------------------
# Sayt sozlamalari
# ---------------------------------------------------------------------------


class SiteSettingsUpdateView(DashboardPermissionMixin, UpdateView):
    """Yagona qatorli forma — URL'da ``pk`` yo'q, doim ``SiteSettings.load()``."""

    required_perms = ["dashboard.manage_settings"]
    form_class = SiteSettingsForm
    template_name = "dashboard/settings_form.html"
    success_url = reverse_lazy("dashboard:site_settings")

    def get_object(self, queryset=None):
        return SiteSettings.load()

    def form_valid(self, form):
        messages.success(self.request, "Sayt sozlamalari saqlandi.")
        return super().form_valid(form)


# ---------------------------------------------------------------------------
# Bannerlar
# ---------------------------------------------------------------------------


class BannerManageListView(DashboardPermissionMixin, ListView):
    required_perms = ["dashboard.manage_banners"]
    model = Banner
    template_name = "dashboard/banner_list.html"
    context_object_name = "banners"
    paginate_by = 20

    def get_queryset(self):
        queryset = Banner.objects.all()
        if position := self.request.GET.get("position"):
            queryset = queryset.filter(position=position)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_position"] = self.request.GET.get("position", "")
        context["position_choices"] = Banner.Position.choices
        return context


class BannerCreateView(DashboardPermissionMixin, CreateView):
    required_perms = ["dashboard.manage_banners"]
    model = Banner
    form_class = BannerForm
    template_name = "dashboard/banner_form.html"
    success_url = reverse_lazy("dashboard:banner_list")

    def form_valid(self, form):
        messages.success(self.request, f"«{form.instance.title}» banneri qo'shildi.")
        return super().form_valid(form)


class BannerUpdateView(DashboardPermissionMixin, UpdateView):
    required_perms = ["dashboard.manage_banners"]
    model = Banner
    form_class = BannerForm
    template_name = "dashboard/banner_form.html"
    success_url = reverse_lazy("dashboard:banner_list")

    def form_valid(self, form):
        messages.success(self.request, f"«{form.instance.title}» banneri yangilandi.")
        return super().form_valid(form)


class BannerDeleteView(DashboardPermissionMixin, DeleteView):
    required_perms = ["dashboard.manage_banners"]
    model = Banner
    template_name = "dashboard/banner_confirm_delete.html"
    success_url = reverse_lazy("dashboard:banner_list")

    def form_valid(self, form):
        messages.success(self.request, f"«{self.object.title}» banneri o'chirildi.")
        return super().form_valid(form)


# ---------------------------------------------------------------------------
# Bosh sahifa bo'limlari
# ---------------------------------------------------------------------------


class HomepageSectionListView(DashboardPermissionMixin, ListView):
    """Bo'limlar ro'yxati + tartiblash (drag-and-drop, AJAX orqali).

    Yaratish/o'chirish yo'q — bo'limlar to'plami ``seed_homepage_sections``
    orqali belgilanadi (asosiy sahifa dizayni shu bo'limlarga tayanadi).
    Admin faqat sarlavha/limit/faollik/tartibni o'zgartira oladi.
    """

    required_perms = ["dashboard.manage_homepage"]
    model = HomepageSection
    template_name = "dashboard/homepage_sections.html"
    context_object_name = "sections"

    def get_queryset(self):
        return HomepageSection.objects.select_related("category", "movie").order_by("order", "id")


class HomepageSectionUpdateView(DashboardPermissionMixin, UpdateView):
    required_perms = ["dashboard.manage_homepage"]
    model = HomepageSection
    form_class = HomepageSectionForm
    template_name = "dashboard/homepage_section_form.html"
    success_url = reverse_lazy("dashboard:homepage_sections")

    def form_valid(self, form):
        messages.success(self.request, f"«{form.instance.title}» bo'limi yangilandi.")
        return super().form_valid(form)


# ---------------------------------------------------------------------------
# Bildirishnomalar
# ---------------------------------------------------------------------------


class NotificationListView(DashboardPermissionMixin, ListView):
    """Yuborilgan bildirishnomalar tarixi -- yetkazish statistikasi bilan."""

    required_perms = ["dashboard.send_notifications"]
    model = Notification
    template_name = "dashboard/notification_list.html"
    context_object_name = "notifications"
    paginate_by = 20

    def get_queryset(self):
        return Notification.objects.select_related("created_by").order_by("-created_at")


class NotificationCreateView(DashboardPermissionMixin, CreateView):
    """Bildirishnoma yaratish -- saqlangan zahoti yuboriladi (dispatch())."""

    required_perms = ["dashboard.send_notifications"]
    model = Notification
    form_class = NotificationForm
    template_name = "dashboard/notification_form.html"
    success_url = reverse_lazy("dashboard:notification_list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        # M2M (target_users) super().form_valid() ichida saqlangandan keyin
        # mavjud bo'ladi, shuning uchun dispatch() shu yerda chaqiriladi.
        sent_count = self.object.dispatch()
        messages.success(
            self.request,
            f"«{self.object.title}» {sent_count} ta foydalanuvchiga yuborildi.",
        )
        return response


class NotificationDetailView(DashboardPermissionMixin, DetailView):
    """Bitta bildirishnomaning yetkazish/o'qilish statistikasi."""

    required_perms = ["dashboard.send_notifications"]
    model = Notification
    template_name = "dashboard/notification_detail.html"
    context_object_name = "notification"

    def get_queryset(self):
        return Notification.objects.select_related("created_by")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["recipients"] = (
            self.object.recipients.select_related("user").order_by("-is_read", "-created_at")[:200]
        )
        return context



# ---------------------------------------------------------------------------
# AJAX harakatlar
# ---------------------------------------------------------------------------


@require_POST
@dashboard_perm_required("movies.change_movie")
def toggle_publish(request, pk):
    """Filmni chop etish / yashirish (AJAX)."""
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
@dashboard_perm_required("movies.change_movie")
def toggle_featured(request, pk):
    """Filmni "tanlangan" qilish / bekor qilish (AJAX)."""
    movie = get_object_or_404(Movie, pk=pk)
    movie.is_featured = not movie.is_featured
    movie.save(update_fields=["is_featured", "updated_at"])

    return JsonResponse({"featured": movie.is_featured})


@require_POST
@dashboard_perm_required("movies.change_movie")
def toggle_trending(request, pk):
    """Filmni "trendda" qilish / bekor qilish (AJAX).

    Yangi toggle sifatida generik "state" kalitini qaytaradi —
    `dashboard.js` dagi `.js-toggle` uni birinchi navbatda tekshiradi.
    """
    movie = get_object_or_404(Movie, pk=pk)
    movie.is_trending = not movie.is_trending
    movie.save(update_fields=["is_trending", "updated_at"])

    trend_note = "trendga qo'shildi" if movie.is_trending else "trenddan olib tashlandi"
    return JsonResponse({"state": movie.is_trending, "message": f"«{movie.title}» {trend_note}"})


@require_POST
@dashboard_perm_required("users.change_user")
def toggle_block(request, pk):
    """Foydalanuvchini bloklash / blokdan chiqarish (AJAX)."""
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
@dashboard_perm_required("reviews.change_review")
def moderate_review(request, pk, action):
    """Sharhni tasdiqlash / rad etish / shikoyat / spam / o'chirish (AJAX)."""
    review = get_object_or_404(Review, pk=pk)

    status_map = {
        "approve": (Review.Status.APPROVED, "Sharh tasdiqlandi"),
        "reject": (Review.Status.REJECTED, "Sharh rad etildi"),
        "report": (Review.Status.REPORTED, "Sharh shikoyat qilingan deb belgilandi"),
        "spam": (Review.Status.SPAM, "Sharh spam deb belgilandi"),
    }

    if action in status_map:
        new_status, message = status_map[action]
        review.status = new_status
        review.save(update_fields=["status", "updated_at"])
        return JsonResponse({"status": new_status, "message": message})

    if action == "delete":
        review.delete()
        return JsonResponse({"status": "deleted", "message": "Sharh o'chirildi"})

    return JsonResponse({"error": "Noma'lum amal"}, status=400)


@require_POST
@dashboard_perm_required("series.change_series")
def toggle_series_publish(request, pk):
    """Serialni chop etish / yashirish (AJAX)."""
    series = get_object_or_404(Series, pk=pk)
    series.is_published = not series.is_published
    series.save(update_fields=["is_published", "updated_at"])

    note = "chop etildi" if series.is_published else "yashirildi"
    return JsonResponse({"state": series.is_published, "message": f"«{series.title}» {note}"})


@require_POST
@dashboard_perm_required("series.change_episode")
def toggle_episode_publish(request, pk):
    """Epizodni chop etish / yashirish (AJAX)."""
    episode = get_object_or_404(Episode, pk=pk)
    episode.is_published = not episode.is_published
    episode.save(update_fields=["is_published", "updated_at"])

    note = "chop etildi" if episode.is_published else "yashirildi"
    return JsonResponse({"state": episode.is_published, "message": f"«{episode.title}» {note}"})


@require_POST
@dashboard_perm_required("dashboard.manage_banners")
def toggle_banner(request, pk):
    """Bannerni faollashtirish / o'chirish (AJAX)."""
    banner = get_object_or_404(Banner, pk=pk)
    banner.is_active = not banner.is_active
    banner.save(update_fields=["is_active", "updated_at"])

    note = "faollashtirildi" if banner.is_active else "o'chirildi"
    return JsonResponse({"state": banner.is_active, "message": f"«{banner.title}» {note}"})


@require_POST
@dashboard_perm_required("dashboard.manage_homepage")
def toggle_section(request, pk):
    """Bosh sahifa bo'limini yoqish / o'chirish (AJAX)."""
    section = get_object_or_404(HomepageSection, pk=pk)
    section.is_active = not section.is_active
    section.save(update_fields=["is_active"])

    note = "yoqildi" if section.is_active else "o'chirildi"
    return JsonResponse({"state": section.is_active, "message": f"«{section.title}» {note}"})


@require_POST
@dashboard_perm_required("dashboard.manage_homepage")
def reorder_sections(request):
    """Bosh sahifa bo'limlarini drag-and-drop orqali qayta tartiblash (AJAX).

    So'rov tanasi: {"order": [id1, id2, id3, ...]} -- ro'yxatdagi
    ketma-ketlik yangi tartibni bildiradi (0 dan boshlab).
    """
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Noto'g'ri so'rov formati."}, status=400)

    ordered_ids = payload.get("order")
    if not isinstance(ordered_ids, list) or not ordered_ids:
        return JsonResponse({"error": "Tartib ro'yxati kerak."}, status=400)

    sections = {s.pk: s for s in HomepageSection.objects.filter(pk__in=ordered_ids)}
    if len(sections) != len(ordered_ids):
        return JsonResponse({"error": "Ba'zi bo'limlar topilmadi."}, status=400)

    for index, section_id in enumerate(ordered_ids):
        section = sections[section_id]
        if section.order != index:
            section.order = index
            section.save(update_fields=["order"])

    return JsonResponse({"message": "Tartib saqlandi."})
