"""Django admin sozlamalari -- sayt konfiguratsiyasi."""

from django.contrib import admin

from .models import Banner, HomepageSection, SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """Yagona qatorli model -- ro'yxatga qo'shish/o'chirish imkonini yopamiz."""

    list_display = ["site_name", "contact_email", "maintenance_mode", "updated_at"]
    readonly_fields = ["updated_at"]

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(HomepageSection)
class HomepageSectionAdmin(admin.ModelAdmin):
    list_display = ["title", "key", "order", "is_active", "item_limit"]
    list_editable = ["order", "is_active"]
    list_filter = ["is_active", "key"]
    autocomplete_fields = ["category", "movie"]


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = [
        "title", "position", "is_active", "is_running",
        "impressions", "clicks", "ctr", "start_date", "end_date",
    ]
    list_editable = ["is_active"]
    list_filter = ["is_active", "position"]
    search_fields = ["title"]
    readonly_fields = ["impressions", "clicks", "created_at", "updated_at"]

    @admin.display(description="CTR", ordering="clicks")
    def ctr(self, obj):
        return f"{obj.ctr}%"

    @admin.display(description="Ishlamoqda", boolean=True)
    def is_running(self, obj):
        return obj.is_running
