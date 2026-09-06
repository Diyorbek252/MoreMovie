"""Django admin sozlamalari — foydalanuvchilar."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Profile, User


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    fields = ["avatar", "bio", "country"]


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = [ProfileInline]
    list_display = [
        "username",
        "email",
        "is_blocked",
        "is_staff",
        "is_active",
        "date_joined",
    ]
    list_filter = ["is_blocked", "is_staff", "is_superuser", "is_active", "date_joined"]
    search_fields = ["username", "email", "first_name", "last_name"]
    ordering = ["-date_joined"]
    actions = ["block_users", "unblock_users"]

    # Standart fieldsets ustiga is_blocked maydonini qo'shamiz.
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Moderatsiya", {"fields": ("is_blocked",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "password1", "password2"),
            },
        ),
    )

    @admin.action(description="Tanlangan foydalanuvchilarni bloklash")
    def block_users(self, request, queryset):
        updated = queryset.update(is_blocked=True)
        self.message_user(request, f"{updated} ta foydalanuvchi bloklandi.")

    @admin.action(description="Tanlangan foydalanuvchilarni blokdan chiqarish")
    def unblock_users(self, request, queryset):
        updated = queryset.update(is_blocked=False)
        self.message_user(request, f"{updated} ta foydalanuvchi blokdan chiqarildi.")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "country", "created_at"]
    search_fields = ["user__username", "user__email"]
    raw_id_fields = ["user"]
