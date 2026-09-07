"""Do'kon — public sahifalar: mahsulotlar ro'yxati va xaridlar tarixi."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from .models import Order, Product


class ProductListView(ListView):
    """Do'kon vitrinasi — barcha faol mahsulotlar."""

    model = Product
    template_name = "shop/product_list.html"
    context_object_name = "products"

    def get_queryset(self):
        return Product.objects.filter(is_active=True)


class OrderHistoryView(LoginRequiredMixin, ListView):
    """Foydalanuvchining o'z xaridlari tarixi ("Xaridlarim")."""

    model = Order
    template_name = "shop/order_history.html"
    context_object_name = "orders"
    paginate_by = 24

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).select_related("product")
