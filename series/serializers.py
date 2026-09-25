"""DRF serializerlari — serial katalogi.

Movie'dan farqli: litsenziya (`LicenseType`) tushunchasi yo'q, shuning
uchun ko'rish ruxsati faqat `Episode.can_watch` (chop etilgan + video bor)
va obuna tekshiruviga tayanadi. Video manba baribir HECH QACHON shartsiz
chiqarilmaydi — `movies/serializers.py` dagi bilan bir xil qoida.
"""

from rest_framework import serializers

from movies.serializers import ActorSerializer, DirectorSerializer, GenreSerializer

from .models import Episode, Season, Series, SeriesCast


class SeriesCastMemberSerializer(serializers.ModelSerializer):
    actor = ActorSerializer(read_only=True)

    class Meta:
        model = SeriesCast
        fields = ["actor", "character_name", "order"]


class SeriesCardSerializer(serializers.ModelSerializer):
    """Ro'yxat/karta ko'rinishi — `MovieCardSerializer` bilan bir xil naqsh."""

    genres = GenreSerializer(many=True, read_only=True)
    user_rating_display = serializers.ReadOnlyField()
    season_count = serializers.ReadOnlyField()
    episode_count = serializers.ReadOnlyField()

    class Meta:
        model = Series
        fields = [
            "id", "title", "slug", "poster", "backdrop", "short_description",
            "release_year", "end_year", "status", "imdb_rating",
            "user_rating_display", "is_featured", "is_trending", "is_premium",
            "genres", "season_count", "episode_count",
        ]


class EpisodeSerializer(serializers.ModelSerializer):
    """Bitta epizod — `?episode=` orqali tanlanadigan pleer ma'lumoti.

    HUQUQIY ESLATMA: `video_source`/`download_url` `SerializerMethodField` —
    faqat `is_watchable_by()` True bo'lganda to'ldiriladi (movies bilan
    bir xil qoida, garchi Series'da litsenziya tushunchasi bo'lmasa ham).
    """

    duration_display = serializers.ReadOnlyField()
    display_thumbnail_url = serializers.ReadOnlyField()
    can_watch = serializers.ReadOnlyField()
    can_play = serializers.SerializerMethodField()
    video_source = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = Episode
        fields = [
            "id", "episode_number", "title", "description",
            "display_thumbnail_url", "duration_display", "air_date",
            "views_count", "can_watch", "can_play", "video_source", "download_url",
        ]

    def _user(self):
        request = self.context.get("request")
        return getattr(request, "user", None)

    def get_can_play(self, obj):
        return obj.is_watchable_by(self._user())

    def get_video_source(self, obj):
        return obj.video_source if self.get_can_play(obj) else ""

    def get_download_url(self, obj):
        if obj.is_download_allowed and obj.download_url and self.get_can_play(obj):
            return obj.download_url
        return None


class SeasonSerializer(serializers.ModelSerializer):
    display_title = serializers.ReadOnlyField()
    episodes = serializers.SerializerMethodField()

    class Meta:
        model = Season
        fields = ["id", "number", "display_title", "poster", "year", "episodes"]

    def get_episodes(self, obj):
        # Faqat chop etilgan epizodlar — `SeriesDetailView` bilan bir xil.
        episodes = [e for e in obj.episodes.all() if e.is_published]
        return EpisodeSerializer(episodes, many=True, context=self.context).data


class SeriesDetailSerializer(SeriesCardSerializer):
    directors = DirectorSerializer(many=True, read_only=True)
    countries = serializers.SlugRelatedField(many=True, read_only=True, slug_field="name")
    language = serializers.SlugRelatedField(read_only=True, slug_field="name")
    cast = SeriesCastMemberSerializer(source="cast_members", many=True, read_only=True)
    seasons = serializers.SerializerMethodField()
    similar_series = serializers.SerializerMethodField()

    class Meta(SeriesCardSerializer.Meta):
        fields = SeriesCardSerializer.Meta.fields + [
            "original_title", "description", "directors", "countries",
            "language", "age_rating", "cast", "seasons", "similar_series",
            "views_count", "trailer_url",
        ]

    def get_seasons(self, obj):
        seasons = obj.seasons.filter(is_published=True).order_by("number")
        return SeasonSerializer(seasons, many=True, context=self.context).data

    def get_similar_series(self, obj):
        from django.db.models import Count

        genre_ids = list(obj.genres.values_list("id", flat=True))
        similar = (
            Series.objects.published()
            .with_relations()
            .filter(genres__id__in=genre_ids)
            .exclude(pk=obj.pk)
            .annotate(shared=Count("genres"))
            .order_by("-shared")
            .distinct()[:12]
        )
        return SeriesCardSerializer(similar, many=True, context=self.context).data
