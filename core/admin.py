"""Django admin sozlamalari — sayt murojaatlari."""

from django.contrib import admin

from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "subject", "is_read", "created_at"]
    list_filter = ["is_read", "created_at"]
    search_fields = ["name", "email", "subject", "message"]
    readonly_fields = ["name", "email", "subject", "message", "created_at"]
    actions = ["mark_read"]

    @admin.action(description="O‘qilgan deb belgilash")
    def mark_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f"{updated} ta murojaat o‘qilgan deb belgilandi.")
