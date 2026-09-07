"""Do'kon — public sahifalar: mahsulotlar ro'yxati va xaridlar tarixi."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.views.generic import ListView

from movies.views import QueryStringMixin

from .models import Order, Product


class ProductListView(QueryStringMixin, ListView):
    """Do'kon vitrinasi — qidiruv, "balansim yetadi" filtri va saralash bilan."""

    model = Product
    template_name = "shop/product_list.html"
    context_object_name = "products"
    paginate_by = 24

    # movies.views.MovieListView bilan bir xil naqsh — foydalanuvchi
    # qiymati to'g'ridan-to'g'ri order_by() ga uzatilmaydi.
    SORT_OPTIONS = {
        "default": ("order", "Standart"),
        "price_asc": ("price", "Narx: arzondan qimmatga"),
        "price_desc": ("-price", "Narx: qimmatdan arzonga"),
        "newest": ("-created_at", "Eng yangi"),
        "az": ("name", "A-Z"),
    }

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True)
        params = self.request.GET

        if query := params.get("q", "").strip():
            queryset = queryset.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )

        # Faqat tizimga kirgan va balansi yetarli bo'lgan foydalanuvchi
        # uchun ma'noga ega — anonim foydalanuvchida balans yo'q.
        user = self.request.user
        if params.get("affordable") == "1" and user.is_authenticated:
            queryset = queryset.filter(price__lte=user.profile.balance)

        sort = params.get("sort", "default")
        order_field = self.SORT_OPTIONS.get(sort, self.SORT_OPTIONS["default"])[0]
        return queryset.order_by(order_field)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        params = self.request.GET

        context.update(
            {
                "sort_options": self.SORT_OPTIONS,
                "current": {
                    "q": params.get("q", ""),
                    "affordable": params.get("affordable", ""),
                    "sort": params.get("sort", "default"),
                },
                "has_filters": any(params.get(key) for key in ("q", "affordable")),
            }
        )
        return context


class OrderHistoryView(LoginRequiredMixin, ListView):
    """Foydalanuvchining o'z xaridlari tarixi ("Xaridlarim")."""

    model = Order
    template_name = "shop/order_history.html"
    context_object_name = "orders"
    paginate_by = 24

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).select_related("product")
