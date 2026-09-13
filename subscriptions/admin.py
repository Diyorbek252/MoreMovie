"""Django admin sozlamalari — obuna tizimi.

Kundalik boshqaruv `dashboard` panelidan amalga oshiriladi (tasdiqlash/rad
etish `subscriptions.services` orqali muddat va bildirishnomani to'g'ri
hisoblaydi); bu yerdagi ro'yxatga olish faqat superuser uchun qo'shimcha
(Django admin) kirish.
"""

from django.contrib import admin

from .models import Plan, PlanPrice, Subscription


class PlanPriceInline(admin.TabularInline):
    model = PlanPrice
    extra = 1


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ["name", "level", "allows_premium_movies", "is_active", "order"]
    list_editable = ["is_active", "order"]
    list_filter = ["is_active", "allows_premium_movies"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ["name"]}
    inlines = [PlanPriceInline]


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ["user", "plan_name", "status", "price_paid", "ends_at", "created_at"]
    list_filter = ["status"]
    search_fields = ["user__username", "plan_name"]
    readonly_fields = ["plan_name", "duration_days", "price_paid", "created_at", "updated_at"]
