"""Django admin sozlamalari -- seriallar (Django admin orqali ham boshqarish
mumkin, asosiy boshqaruv esa /dashboard/ panelida)."""

from django.contrib import admin
from django.utils.html import format_html

from .models import Episode, Season, Series, SeriesCast


class SeriesCastInline(admin.TabularInline):
    model = SeriesCast
    extra = 3
    autocomplete_fields = ["actor"]
    fields = ["actor", "character_name", "order"]


class SeasonInline(admin.TabularInline):
    model = Season
    extra = 1
    fields = ["number", "title", "year", "is_published"]
    show_change_link = True


@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    list_display = [
        "poster_thumb", "title", "release_year", "status",
        "is_published", "is_featured", "is_trending", "views_count",
    ]
    list_display_links = ["poster_thumb", "title"]
    list_editable = ["is_published", "is_featured", "is_trending"]
    list_filter = ["is_published", "is_featured", "is_trending", "status", "genres", "release_year"]
    search_fields = ["title", "original_title", "description", "directors__full_name"]
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ["country", "language"]
    filter_horizontal = ["genres", "categories", "directors"]
    inlines = [SeasonInline, SeriesCastInline]
    readonly_fields = ["views_count", "created_at", "updated_at"]

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related("country", "language")
            .prefetch_related("directors")
        )

    @admin.display(description="poster")
    def poster_thumb(self, obj):
        if obj.poster:
            return format_html(
                '<img src="{}" style="height:52px;border-radius:4px;object-fit:cover;">',
                obj.poster.url,
            )
        return "-"


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ["series", "number", "display_title", "episode_count", "is_published"]
    list_filter = ["is_published", "series"]
    search_fields = ["series__title", "title"]
    autocomplete_fields = ["series"]


@admin.register(Episode)
class EpisodeAdmin(admin.ModelAdmin):
    list_display = [
        "season", "episode_number", "title", "duration_display",
        "is_published", "views_count", "downloads_count",
    ]
    list_filter = ["is_published", "quality"]
    search_fields = ["title", "season__series__title"]
    autocomplete_fields = ["season", "language"]
    readonly_fields = ["views_count", "downloads_count", "created_at", "updated_at"]
