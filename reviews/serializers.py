"""DRF serializerlari — reyting va sharh.

Film HAM serial baholanishi/sharh qoldirilishi mumkin — yozish
serializerlarida `movie` XOR `series` tekshiruvi `validate()` da
`reviews/api.py::_resolve_target` bilan bir xil mantiqda takrorlanadi
(DB darajasidagi `CheckConstraint` — `reviews/models.py:50-56` — bilan mos).
"""

from django.shortcuts import get_object_or_404
from rest_framework import serializers

from .models import Rating, Review


class ReviewAuthorSerializer(serializers.Serializer):
    """Sharh ostida ko'rsatiladigan minimal foydalanuvchi ma'lumoti."""

    username = serializers.CharField()
    display_name = serializers.CharField()
    avatar_url = serializers.SerializerMethodField()

    def get_avatar_url(self, obj):
        return obj.profile.avatar_url


class ReviewSerializer(serializers.ModelSerializer):
    """Faqat o'qish — film/serial sahifasidagi tasdiqlangan sharhlar ro'yxati."""

    user = ReviewAuthorSerializer(read_only=True)
    user_score = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ["id", "user", "comment", "user_score", "created_at"]

    def get_user_score(self, obj):
        """`Review.user_score` bilan bir xil natija, lekin N+1'siz —
        ro'yxat view'i `context["ratings_map"]` ni bir so'rov bilan
        oldindan tayyorlaydi (qarang: reviews/api_v1.py)."""
        ratings_map = self.context.get("ratings_map")
        if ratings_map is not None:
            return ratings_map.get(obj.user_id)
        return obj.user_score


class TargetMixin(serializers.Serializer):
    """`movie` XOR `series` maydonini tekshiradi va haqiqiy obyektga
    aylantiradi — `reviews/api.py::_resolve_target` bilan bir xil mantiq.

    `serializers.Serializer` dan MERos qiladi (oddiy mixin emas) — DRF
    fieldlarni `SerializerMetaclass` orqali `_declared_fields`ga faqat
    shu klasslarning avlodlaridan yig'adi; oddiy mixin bo'lsa `movie`/
    `series` fieldlari avlod serializerlarga umuman o'tmay qolar edi.

    ID'lar ataylab oddiy `IntegerField` — `PrimaryKeyRelatedField`ni
    ikkala (movie/series) queryset bilan shartli ishlatish assertion
    xatosiga olib keladi (`required=False` bo'lsa ham `queryset` doim
    kerak), shuning uchun obyekt qidirish qo'lda `validate()` da bajariladi.
    """

    movie = serializers.IntegerField(required=False, allow_null=True)
    series = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, data):
        movie_id = data.get("movie")
        series_id = data.get("series")
        if bool(movie_id) == bool(series_id):
            raise serializers.ValidationError(
                "Film yoki serial — ikkalasidan ANIQ BITTASI ko'rsatilishi kerak."
            )

        # Lokal import — aylanma importning oldini oladi (movies/series
        # modeli reviews'ga bog'liq emas, faqat shu yerda kerak).
        from movies.models import Movie
        from series.models import Series

        if movie_id:
            data["target"] = get_object_or_404(Movie.objects.published(), pk=movie_id)
            data["field_name"] = "movie"
        else:
            data["target"] = get_object_or_404(Series.objects.published(), pk=series_id)
            data["field_name"] = "series"
        return data


class RateSerializer(TargetMixin):
    """`POST /api/v1/ratings/` — `reviews/api.py::rate_movie` DRF ekvivalenti."""

    score = serializers.IntegerField(min_value=1, max_value=5)

    def save(self, **kwargs):
        user = self.context["request"].user
        target = self.validated_data["target"]
        field_name = self.validated_data["field_name"]
        rating, created = Rating.objects.update_or_create(
            user=user, **{field_name: target}, defaults={"score": self.validated_data["score"]}
        )
        # Rating.save() target.recalculate_rating() ni chaqirgan — yangi qiymatni o'qiymiz.
        # Faqat moderatsiyadan o'tgan sharh egalarining bahosi hisoblanadi,
        # shuning uchun bu baho o'rtachaga hali kirmagan bo'lishi mumkin.
        target.refresh_from_db(fields=["avg_rating", "rating_count"])
        self._rating = rating
        self._target = target
        self._created = created
        return rating


class ReviewWriteSerializer(TargetMixin):
    """`POST /api/v1/reviews/` — `reviews/api.py::submit_review` DRF ekvivalenti."""

    comment = serializers.CharField(min_length=10, max_length=2000, trim_whitespace=True)

    def save(self, **kwargs):
        user = self.context["request"].user
        target = self.validated_data["target"]
        field_name = self.validated_data["field_name"]
        # Tahrirlangan sharh qaytadan moderatsiyaga tushadi.
        review, created = Review.objects.update_or_create(
            user=user,
            **{field_name: target},
            defaults={"comment": self.validated_data["comment"], "status": Review.Status.PENDING},
        )
        self._created = created
        return review
