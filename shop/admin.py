"""Django admin sozlamalari — cinepoint do'koni.

Kundalik boshqaruv `dashboard` panelidan amalga oshiriladi; bu yerdagi
ro'yxatga olish faqat superuser uchun qo'shimcha (Django admin) kirish.
"""

from django.contrib import admin

from .models import CinepointTransaction, Order, Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "price", "stock", "is_active", "order"]
    list_editable = ["is_active", "order"]
    list_filter = ["is_active"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ["name"]}


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["user", "product_name", "price_paid", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["user__username", "product_name"]
    readonly_fields = ["product_name", "price_paid", "created_at", "updated_at"]


@admin.register(CinepointTransaction)
class CinepointTransactionAdmin(admin.ModelAdmin):
    list_display = ["user", "amount", "reason", "created_at"]
    list_filter = ["reason"]
    search_fields = ["user__username", "note"]
    readonly_fields = [
        "user", "amount", "reason", "note",
        "content_type", "object_id", "created_by", "created_at",
    ]

    def has_add_permission(self, request):
        # Tranzaksiyalar faqat shop.services.adjust_balance() orqali
        # yaratiladi — admin panelida qo'lda qo'shish yo'q.
        return False
