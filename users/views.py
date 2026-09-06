"""Autentifikatsiya va foydalanuvchi sahifalari."""

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as BaseLoginView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, TemplateView

from movies.models import Favorite, ViewHistory, Watchlist
from reviews.models import Review

from .forms import LoginForm, ProfileForm, RegisterForm, UserForm


class RegisterView(CreateView):
    """Ro'yxatdan o'tish — muvaffaqiyatli bo'lsa darhol tizimga kiritadi."""

    form_class = RegisterForm
    template_name = "users/register.html"
    success_url = reverse_lazy("core:home")

    def dispatch(self, request, *args, **kwargs):
        # Allaqachon kirgan foydalanuvchini bosh sahifaga yuboramiz.
        if request.user.is_authenticated:
            return redirect("core:home")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        # Backend'ni aniq ko'rsatamiz — ikkita backend sozlangani uchun shart.
        login(self.request, self.object, backend="users.backends.EmailOrUsernameBackend")
        messages.success(
            self.request,
            f"Xush kelibsiz, {self.object.username}! Hisobingiz yaratildi.",
        )
        return response


class LoginView(BaseLoginView):
    """Kirish — "Meni eslab qol" sessiya muddatini boshqaradi."""

    form_class = LoginForm
    template_name = "users/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        remember = form.cleaned_data.get("remember_me")
        if not remember:
            # Belgilanmagan bo'lsa — brauzer yopilganda sessiya tugaydi.
            self.request.session.set_expiry(0)

        response = super().form_valid(form)
        messages.success(self.request, f"Xush kelibsiz, {self.request.user.username}!")
        return response


class ProfileView(LoginRequiredMixin, TemplateView):
    """Foydalanuvchi profili — statistika va oxirgi faoliyat."""

    template_name = "users/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context["watchlist_count"] = Watchlist.objects.filter(user=user).count()
        context["favorite_count"] = Favorite.objects.filter(user=user).count()
        context["watched_count"] = ViewHistory.objects.filter(user=user).count()
        context["review_count"] = Review.objects.filter(user=user).count()

        # Oxirgi ko'rilgan filmlar.
        context["recent_history"] = (
            ViewHistory.objects.filter(user=user)
            .select_related("movie", "movie__country", "movie__language", "movie__director")
            .prefetch_related("movie__genres")[:12]
        )

        # Foydalanuvchining sharhlari — holati bilan birga.
        context["my_reviews"] = (
            Review.objects.filter(user=user).select_related("movie").order_by("-created_at")[:10]
        )

        return context


@login_required
def profile_edit(request):
    """Profil tahriri — User va Profile formalari birga saqlanadi."""
    user_form = UserForm(request.POST or None, instance=request.user)
    profile_form = ProfileForm(
        request.POST or None, request.FILES or None, instance=request.user.profile
    )

    if request.method == "POST":
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Profil ma'lumotlaringiz saqlandi.")
            return redirect("users:profile")
        messages.error(request, "Formada xatolik bor — quyidagilarni tekshiring.")

    return render(
        request,
        "users/profile_edit.html",
        {"user_form": user_form, "profile_form": profile_form},
    )


class WatchlistView(LoginRequiredMixin, ListView):
    """Keyinroq ko'rish uchun saqlangan filmlar."""

    template_name = "users/watchlist.html"
    context_object_name = "entries"
    paginate_by = 24

    def get_queryset(self):
        return (
            Watchlist.objects.filter(user=self.request.user)
            .select_related("movie", "movie__country", "movie__language", "movie__director")
            .prefetch_related("movie__genres")
        )


class FavoritesView(LoginRequiredMixin, ListView):
    """Sevimli filmlar."""

    template_name = "users/favorites.html"
    context_object_name = "entries"
    paginate_by = 24

    def get_queryset(self):
        return (
            Favorite.objects.filter(user=self.request.user)
            .select_related("movie", "movie__country", "movie__language", "movie__director")
            .prefetch_related("movie__genres")
        )
