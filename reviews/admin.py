"""Django admin sozlamalari — reyting va sharhlar."""

from django.contrib import admin

from .models import Rating, Review


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ["user", "movie", "score", "updated_at"]
    list_filter = ["score", "updated_at"]
    search_fields = ["user__username", "movie__title"]
    autocomplete_fields = ["movie"]
    raw_id_fields = ["user"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "movie")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["user", "movie", "status", "short_comment", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["user__username", "movie__title", "comment"]
    autocomplete_fields = ["movie"]
    raw_id_fields = ["user"]
    actions = ["approve_reviews", "reject_reviews"]
    readonly_fields = ["created_at", "updated_at"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "movie")

    @admin.display(description="sharh")
    def short_comment(self, obj):
        return obj.comment[:80] + ("..." if len(obj.comment) > 80 else "")

    @admin.action(description="Tanlangan sharhlarni tasdiqlash")
    def approve_reviews(self, request, queryset):
        movies = {review.movie for review in queryset}
        updated = queryset.update(status=Review.Status.APPROVED)
        # queryset.update() save() ni chaqirmaydi — filmlarning o'rtacha
        # reytingini qo'lda qayta hisoblaymiz.
        for movie in movies:
            movie.recalculate_rating()
        self.message_user(request, f"{updated} ta sharh tasdiqlandi.")

    @admin.action(description="Tanlangan sharhlarni rad etish")
    def reject_reviews(self, request, queryset):
        movies = {review.movie for review in queryset}
        updated = queryset.update(status=Review.Status.REJECTED)
        for movie in movies:
            movie.recalculate_rating()
        self.message_user(request, f"{updated} ta sharh rad etildi.")
