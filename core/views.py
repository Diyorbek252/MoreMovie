"""Sayt darajasidagi sahifalar: home, about, contact, huquqiy sahifalar."""

from django.contrib import messages
from django.core.cache import cache
from django.db.models import Count, Q
from django.shortcuts import redirect, render
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy

from movies.models import Genre, Movie, ViewHistory

from .forms import ContactForm

# Bosh sahifa bo'limlarini keshlash muddati (soniya).
HOME_CACHE_TTL = 300


class HomeView(TemplateView):
    """Bosh sahifa — hero + bir nechta karusel bo'lim.

    Bo'limlar barcha foydalanuvchilar uchun bir xil, shuning uchun ular
    keshlanadi. Foydalanuvchiga xos qism ("Davom ettirish") keshlanmaydi.
    """

    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self._get_shared_sections())

        # Foydalanuvchiga xos bo'lim — keshdan tashqarida.
        user = self.request.user
        if user.is_authenticated:
            context["continue_watching"] = (
                ViewHistory.objects.filter(user=user, is_finished=False, progress_seconds__gt=30)
                .select_related("movie", "movie__country", "movie__language", "movie__director")
                .prefetch_related("movie__genres")[:12]
            )

        return context

    def _get_shared_sections(self):
        """Umumiy bo'limlarni keshdan oladi, bo'lmasa hisoblab keshga yozadi."""
        cached = cache.get("home_sections")
        if cached is not None:
            return cached

        published = Movie.objects.published()

        # Hero uchun: tanlangan filmlar orasidan backdrop'i bori.
        hero = published.with_relations().filter(is_featured=True).exclude(backdrop="").first()
        if hero is None:
            hero = published.with_relations().first()

        sections = {
            "hero": hero,
            "trending": list(Movie.objects.trending()[:14]),
            "popular": list(Movie.objects.trending()[:14]),
            "new_releases": list(Movie.objects.newest()[:14]),
            "top_rated": list(Movie.objects.top_rated()[:14]),
            "featured": list(Movie.objects.featured()[:14]),
            # Faqat filmi bor janrlar ko'rsatiladi.
            "genres": list(
                Genre.objects.annotate(
                    movie_total=Count("movies", filter=Q(movies__is_published=True))
                )
                .filter(movie_total__gt=0)
                .order_by("-movie_total")[:10]
            ),
        }

        # "Popular" va "Trending" bir xil bo'lmasligi uchun popularni siljitamiz.
        sections["popular"] = list(Movie.objects.trending()[14:28]) or sections["trending"]

        cache.set("home_sections", sections, HOME_CACHE_TTL)
        return sections


class AboutView(TemplateView):
    template_name = "core/about.html"


class PrivacyView(TemplateView):
    template_name = "core/privacy.html"


class TermsView(TemplateView):
    template_name = "core/terms.html"


class ContactView(CreateView):
    """Murojaat formasi — xabar bazaga yoziladi."""

    form_class = ContactForm
    template_name = "core/contact.html"
    success_url = reverse_lazy("core:contact")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            "Xabaringiz yuborildi. Tez orada siz bilan bog'lanamiz.",
        )
        return response

    def form_invalid(self, form):
        messages.error(self.request, "Formada xatolik bor — quyidagilarni tekshiring.")
        return super().form_invalid(form)


# ---------------------------------------------------------------------------
# Xato sahifalari
# ---------------------------------------------------------------------------


def error_404(request, exception=None):
    return render(request, "errors/404.html", status=404)


def error_403(request, exception=None):
    return render(request, "errors/403.html", status=403)


def error_500(request):
    return render(request, "errors/500.html", status=500)
