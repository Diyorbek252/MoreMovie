"""DRF serializerlari — film katalogi.

HUQUQIY ESLATMA: `video_sources` va `download_url` HECH QACHON shartsiz
chiqarilmaydi. Ikkalasi ham `SerializerMethodField` — ichida
`Movie.is_watchable_by()` / `Movie.can_download` tekshiriladi. Aks holda
premium yoki `trailer_only` kontentning video havolasi JSON orqali
DevTools'da ochilib qoladi (shablonda `{% if can_play %}` o'rnini bosadi).
"""

from rest_framework import serializers

from .models import Actor, Director, Favorite, Genre, Movie, MovieCast, Screenshot, Watchlist


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ["id", "name", "slug", "icon"]


class DirectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Director
        fields = ["id", "full_name", "slug", "photo"]


class ActorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = ["id", "full_name", "slug", "photo"]


class CastMemberSerializer(serializers.ModelSerializer):
    """`MovieCast` orqali — aktyor + shu filmdagi rol nomi."""

    actor = ActorSerializer(read_only=True)

    class Meta:
        model = MovieCast
        fields = ["actor", "character_name", "order"]


class ScreenshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Screenshot
        fields = ["id", "image", "caption", "order"]


class MovieCardSerializer(serializers.ModelSerializer):
    """`templates/partials/movie_card.html` ga mos yengil serializer.

    Ro'yxat sahifalarida ishlatiladi — CLAUDE.md dagi "bitta kartochka
    shabloni" qoidasining API ekvivalenti: yangi ro'yxat uchun yangi
    serializer yozmang, shuni ishlating.
    """

    genres = GenreSerializer(many=True, read_only=True)
    duration_display = serializers.ReadOnlyField()
    quality_badges = serializers.ReadOnlyField()
    user_rating_display = serializers.ReadOnlyField()
    premiere_label = serializers.ReadOnlyField()
    is_upcoming_premiere = serializers.ReadOnlyField()
    can_watch = serializers.ReadOnlyField()
    in_watchlist = serializers.SerializerMethodField()
    in_favorite = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = [
            "id", "kind", "title", "slug", "poster", "backdrop",
            "short_description", "release_year", "duration_display",
            "quality_badges", "imdb_rating", "user_rating_display",
            "is_premiere", "premiere_label", "is_upcoming_premiere",
            "premiere_date", "is_featured", "is_trending", "is_premium",
            "can_watch", "genres", "in_watchlist", "in_favorite",
        ]

    def _ids_set(self, key):
        """Kontekstda oldindan hisoblangan to'plamni ishlatadi — bo'lmasa
        (masalan detail view'da) bitta so'rov bilan hisoblaydi.

        `core.context_processors.site_globals` dagi
        `user_watchlist_ids`/`user_favorite_ids` naqshining API ekvivalenti:
        har karta uchun alohida so'rov qilinmaydi.
        """
        if key in self.context:
            return self.context[key]
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return set()
        model = Watchlist if key == "user_watchlist_ids" else Favorite
        return set(model.objects.filter(user=user).values_list("movie_id", flat=True))

    def get_in_watchlist(self, obj):
        return obj.id in self._ids_set("user_watchlist_ids")

    def get_in_favorite(self, obj):
        return obj.id in self._ids_set("user_favorite_ids")


class MovieDetailSerializer(MovieCardSerializer):
    """Film detail sahifasi — `MovieDetailView.get_context_data` ekvivalenti."""

    directors = DirectorSerializer(many=True, read_only=True)
    countries = serializers.SlugRelatedField(many=True, read_only=True, slug_field="name")
    language = serializers.SlugRelatedField(read_only=True, slug_field="name")
    meta_description_text = serializers.ReadOnlyField()
    best_quality_display = serializers.ReadOnlyField()
    can_play = serializers.SerializerMethodField()
    video_sources = serializers.SerializerMethodField()
    can_download = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()
    resume_at = serializers.SerializerMethodField()
    user_rating = serializers.SerializerMethodField()
    cast = CastMemberSerializer(source="cast_members", many=True, read_only=True)
    screenshots = ScreenshotSerializer(many=True, read_only=True)
    similar_movies = serializers.SerializerMethodField()
    license_type_display = serializers.CharField(source="get_license_type_display", read_only=True)

    class Meta(MovieCardSerializer.Meta):
        fields = MovieCardSerializer.Meta.fields + [
            "original_title", "description", "meta_description_text",
            "directors", "countries", "language", "age_rating",
            "best_quality_display", "can_play", "video_sources",
            "can_download", "download_url", "resume_at", "user_rating",
            "views_count", "cast", "screenshots", "similar_movies",
            # Huquqiy holat — detail sahifadagi litsenziya bildirishnomasi
            # va treyler-fallback shu maydonlarga tayanadi. `video_sources`
            # kabi bular ham "ma'lumot", ochish RUXSATI emas — pleer
            # baribir faqat `can_play` orqali ochiladi.
            "trailer_url", "license_type", "license_type_display", "license_note",
        ]

    def _request_user(self):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        return user if user and user.is_authenticated else None

    def get_can_play(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        return obj.is_watchable_by(user)

    def get_video_sources(self, obj):
        """Shartsiz HECH QACHON qaytarilmaydi — `can_play` False bo'lsa
        bo'sh ro'yxat (`is_watchable_by` litsenziya VA obunani tekshiradi)."""
        if not self.get_can_play(obj):
            return []
        return obj.video_sources

    def get_can_download(self, obj):
        return obj.can_download

    def get_download_url(self, obj):
        return obj.download_url if obj.can_download else None

    def get_resume_at(self, obj):
        user = self._request_user()
        if not user:
            return 0
        from .models import ViewHistory

        history = ViewHistory.objects.filter(user=user, movie=obj).first()
        return history.progress_seconds if history else 0

    def get_user_rating(self, obj):
        user = self._request_user()
        if not user:
            return 0
        from reviews.models import Rating

        rating = Rating.objects.filter(user=user, movie=obj).first()
        return rating.score if rating else 0

    def get_similar_movies(self, obj):
        """`MovieDetailView.get_context_data` dagi bir xil janr mantig'i —
        mos janrlar soni bo'yicha, eng ko'p 12 ta."""
        from django.db.models import Count

        genre_ids = list(obj.genres.values_list("id", flat=True))
        similar = (
            Movie.objects.published()
            .with_relations()
            .filter(genres__id__in=genre_ids)
            .exclude(pk=obj.pk)
            .annotate(shared=Count("genres"))
            .order_by("-shared", "-avg_rating")
            .distinct()[:12]
        )
        return MovieCardSerializer(similar, many=True, context=self.context).data
