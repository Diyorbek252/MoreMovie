"""Django admin sozlamalari — filmlar katalogi."""

from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Actor,
    Category,
    Country,
    Director,
    Favorite,
    Genre,
    Language,
    Movie,
    MovieCast,
    Screenshot,
    ViewHistory,
    Watchlist,
)


class MovieCastInline(admin.TabularInline):
    model = MovieCast
    extra = 3
    autocomplete_fields = ["actor"]
    fields = ["actor", "character_name", "order"]


class ScreenshotInline(admin.TabularInline):
    model = Screenshot
    extra = 2
    fields = ["image", "caption", "order"]


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "movie_count", "order"]
    list_editable = ["order"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}

    @admin.display(description="filmlar")
    def movie_count(self, obj):
        return obj.movies.count()


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "movie_count", "order", "is_active"]
    list_editable = ["order", "is_active"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}

    @admin.display(description="filmlar")
    def movie_count(self, obj):
        return obj.movies.count()


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ["name", "code"]
    search_fields = ["name", "code"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ["name", "code"]
    search_fields = ["name", "code"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Director)
class DirectorAdmin(admin.ModelAdmin):
    list_display = ["full_name", "directed_count"]
    search_fields = ["full_name"]
    prepopulated_fields = {"slug": ("full_name",)}

    @admin.display(description="filmlar")
    def directed_count(self, obj):
        return obj.directed_movies.count()


@admin.register(Actor)
class ActorAdmin(admin.ModelAdmin):
    list_display = ["full_name", "acted_count"]
    search_fields = ["full_name"]
    prepopulated_fields = {"slug": ("full_name",)}

    @admin.display(description="rollar")
    def acted_count(self, obj):
        return obj.roles.count()


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = [
        "poster_thumb",
        "title",
        "release_year",
        "quality",
        "license_badge",
        "is_published",
        "is_featured",
        "is_trending",
        "views_count",
        "avg_rating",
    ]
    list_display_links = ["poster_thumb", "title"]
    list_editable = ["is_published", "is_featured", "is_trending"]
    list_filter = [
        "is_published",
        "is_featured",
        "is_trending",
        "is_premium",
        "license_type",
        "quality",
        "age_rating",
        "genres",
        "categories",
        "release_year",
        "country",
        "language",
    ]
    search_fields = ["title", "original_title", "description", "directors__full_name"]
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ["country", "language"]
    filter_horizontal = ["genres", "categories", "directors"]
    inlines = [MovieCastInline, ScreenshotInline]
    readonly_fields = [
        "views_count", "downloads_count", "avg_rating", "rating_count",
        "created_at", "updated_at",
    ]
    date_hierarchy = "created_at"
    actions = ["publish_movies", "unpublish_movies"]

    fieldsets = [
        (
            "Asosiy ma'lumot",
            {
                "fields": [
                    "title",
                    "original_title",
                    "slug",
                    "description",
                    "short_description",
                ]
            },
        ),
        (
            "Media",
            {
                "fields": [
                    "poster",
                    "backdrop",
                    "trailer_url",
                    "video_url",
                    "video_file",
                    "download_url",
                ]
            },
        ),
        (
            "Tasnif",
            {
                "fields": [
                    "genres",
                    "categories",
                    "country",
                    "language",
                    "directors",
                    "release_year",
                    "release_date",
                    "duration_minutes",
                    "quality",
                    "age_rating",
                    "imdb_rating",
                ]
            },
        ),
        (
            "Huquqiy holat",
            {
                "description": (
                    "DIQQAT: to'liq filmni ko'rish va yuklab olish faqat public "
                    "domain yoki litsenziyalangan kontent uchun ochiladi."
                ),
                "fields": ["license_type", "license_note", "is_download_allowed"],
            },
        ),
        ("Chop etish", {"fields": ["is_published", "is_featured", "is_trending", "is_premium"]}),
        (
            "Statistika (avtomatik)",
            {
                "classes": ["collapse"],
                "fields": [
                    "views_count",
                    "downloads_count",
                    "avg_rating",
                    "rating_count",
                    "created_at",
                    "updated_at",
                ],
            },
        ),
        ("SEO", {"classes": ["collapse"], "fields": ["meta_description"]}),
    ]

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
        return "—"

    @admin.display(description="litsenziya")
    def license_badge(self, obj):
        colors = {
            Movie.LicenseType.PUBLIC_DOMAIN: "#2e7d32",
            Movie.LicenseType.LICENSED: "#1565c0",
            Movie.LicenseType.TRAILER_ONLY: "#8d6e00",
        }
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:10px;font-size:11px;">{}</span>',
            colors.get(obj.license_type, "#555"),
            obj.get_license_type_display(),
        )

    @admin.action(description="Tanlanganlarni chop etish")
    def publish_movies(self, request, queryset):
        updated = queryset.update(is_published=True)
        self.message_user(request, f"{updated} ta film chop etildi.")

    @admin.action(description="Tanlanganlarni chop etishdan olib tashlash")
    def unpublish_movies(self, request, queryset):
        updated = queryset.update(is_published=False)
        self.message_user(request, f"{updated} ta film yashirildi.")


@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ["user", "movie", "added_at"]
    list_filter = ["added_at"]
    search_fields = ["user__username", "movie__title"]
    autocomplete_fields = ["movie"]
    raw_id_fields = ["user"]


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ["user", "movie", "added_at"]
    list_filter = ["added_at"]
    search_fields = ["user__username", "movie__title"]
    autocomplete_fields = ["movie"]
    raw_id_fields = ["user"]


@admin.register(ViewHistory)
class ViewHistoryAdmin(admin.ModelAdmin):
    list_display = ["user", "movie", "progress_seconds", "is_finished", "watched_at"]
    list_filter = ["is_finished", "watched_at"]
    search_fields = ["user__username", "movie__title"]
    autocomplete_fields = ["movie"]
    raw_id_fields = ["user"]
