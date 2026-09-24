"""DRF API — reyting berish, sharh yuborish, tasdiqlangan sharhlar ro'yxati."""

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .models import Rating, Review
from .serializers import RateSerializer, ReviewSerializer, ReviewWriteSerializer


class RateView(APIView):
    """`POST /api/v1/ratings/`  body: {"movie": <id>, "score": 1..5} yoki {"series": <id>, ...}"""

    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "write"

    def post(self, request):
        serializer = RateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        target = serializer._target
        rating = serializer._rating
        display = target.user_rating_display

        return Response(
            {
                "score": rating.score,
                "average": float(target.avg_rating),
                "count": target.rating_count,
                "user_rating": f"{display:.1f}" if display is not None else None,
                "message": "Bahoyingiz qabul qilindi" if serializer._created else "Bahoyingiz yangilandi",
            }
        )


class ReviewCreateView(APIView):
    """`POST /api/v1/reviews/`  body: {"movie": <id>, "comment": "..."} yoki {"series": <id>, ...}

    Sharh moderatsiyaga tushadi — tasdiqlangunicha saytda ko'rinmaydi.
    """

    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "write"

    def post(self, request):
        serializer = ReviewWriteSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        review = serializer.save()

        return Response(
            {
                "created": serializer._created,
                "status": review.status,
                "message": (
                    "Sharhingiz yuborildi va moderatsiyadan keyin chop etiladi."
                    if serializer._created
                    else "Sharhingiz yangilandi va qayta moderatsiyaga yuborildi."
                ),
            },
            status=status.HTTP_201_CREATED if serializer._created else status.HTTP_200_OK,
        )


class ReviewListView(generics.ListAPIView):
    """`GET /api/v1/reviews/?movie=<slug>` yoki `?series=<slug>` — tasdiqlangan sharhlar.

    `MovieDetailView.get_context_data` dagi `reviews` konteksti bilan bir
    xil natija (faqat APPROVED, eng oxirgi 20 tasi).
    """

    serializer_class = ReviewSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = Review.objects.filter(status=Review.Status.APPROVED).select_related(
            "user", "user__profile"
        )
        if movie_slug := self.request.query_params.get("movie"):
            queryset = queryset.filter(movie__slug=movie_slug)
        elif series_slug := self.request.query_params.get("series"):
            queryset = queryset.filter(series__slug=series_slug)
        else:
            return queryset.none()
        return queryset.order_by("-created_at")[:20]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # N+1'ning oldini olish uchun — har bir sharh egasining AYNAN shu
        # film/serialga bergan bahosini bir so'rov bilan oldindan
        # tayyorlaymiz (qarang: Review.user_score, ReviewSerializer.get_user_score).
        if movie_slug := self.request.query_params.get("movie"):
            ratings = Rating.objects.filter(movie__slug=movie_slug).values("user_id", "score")
        elif series_slug := self.request.query_params.get("series"):
            ratings = Rating.objects.filter(series__slug=series_slug).values("user_id", "score")
        else:
            ratings = Rating.objects.none()
        context["ratings_map"] = {r["user_id"]: r["score"] for r in ratings}
        return context
