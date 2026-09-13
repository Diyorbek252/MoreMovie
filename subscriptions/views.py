"""Do'kon `shop/views.py` bilan bir xil naqsh — public sahifalar."""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import CreateView, ListView, TemplateView

from siteconfig.models import SiteSettings

from .forms import SubscriptionRequestForm
from .models import Plan, PlanPrice, Subscription
from .services import get_active_subscription, notify_admins_new_subscription


class PlanListView(ListView):
    """Narxlar sahifasi — `/obuna/`."""

    model = Plan
    template_name = "subscriptions/plan_list.html"
    context_object_name = "plans"

    def get_queryset(self):
        return Plan.objects.filter(is_active=True).prefetch_related("prices")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["site_settings"] = SiteSettings.load()
        return context


class SubscriptionRequestView(LoginRequiredMixin, CreateView):
    """Reja tanlab, to'lov isbotini yuboradigan forma.

    Oddiy forma POST ishlatiladi (AJAX emas) — chek fayli yuklanadi va
    natija butun sahifa holatining o'zgarishi ("tasdiq kutilmoqda"),
    inline toggle emas.
    """

    model = Subscription
    form_class = SubscriptionRequestForm
    template_name = "subscriptions/subscription_request.html"

    def dispatch(self, request, *args, **kwargs):
        self.plan = get_object_or_404(Plan, slug=kwargs["slug"], is_active=True)
        return super().dispatch(request, *args, **kwargs)

    def get_price(self):
        """Tanlangan muddat — POST'da (yuborishda) yoki GET'da (?muddat=)
        ko'rsatilgan `PlanPrice.pk`. Topilmasa eng arzoni ishlatiladi.
        """
        price_id = self.request.POST.get("price") or self.request.GET.get("muddat")
        queryset = PlanPrice.objects.filter(plan=self.plan, is_active=True)
        if price_id:
            price = queryset.filter(pk=price_id).first()
            if price:
                return price
        return queryset.order_by("duration_days").first()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["plan"] = self.plan
        context["prices"] = self.plan.prices.filter(is_active=True)
        context["selected_price"] = self.get_price()
        context["site_settings"] = SiteSettings.load()
        return context

    def form_valid(self, form):
        price = self.get_price()
        if price is None:
            messages.error(self.request, "Bu reja uchun hozircha narx belgilanmagan.")
            return redirect("subscriptions:plan_list")

        subscription = form.save(commit=False)
        subscription.user = self.request.user
        subscription.plan = self.plan
        subscription.plan_name = self.plan.name
        subscription.duration_days = price.duration_days
        subscription.price_paid = price.price
        subscription.status = Subscription.Status.PENDING
        subscription.save()

        notify_admins_new_subscription(subscription)
        messages.success(
            self.request,
            "So'rovingiz qabul qilindi — to'lov tekshirilgach obunangiz faollashadi.",
        )
        return redirect("subscriptions:my_subscription")


class MySubscriptionView(LoginRequiredMixin, TemplateView):
    """Foydalanuvchining joriy holati va so'rovlar tarixi."""

    template_name = "subscriptions/my_subscription.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["subscriptions"] = Subscription.objects.filter(
            user=self.request.user
        ).select_related("plan")
        # `is_currently_active` ni ham hisobga oladi (masalan `expire_subscriptions`
        # komandasi hali ishlamagan bo'lsa ham muddati o'tgan obuna qaytmaydi).
        context["active_subscription"] = get_active_subscription(self.request.user)
        return context
