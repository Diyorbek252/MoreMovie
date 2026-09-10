"""Rol -> ruxsatlar lug'ati.

Bu konfiguratsiya, sxema emas — shuning uchun migratsiya emas, balki
``seed_roles`` boshqaruv komandasi orqali bazaga yoziladi (qarang:
``dashboard/management/commands/seed_roles.py``). Rolni o'zgartirish
kerak bo'lsa shu yerni tahrirlab, komandani qayta ishga tushiring.

Har bir qiymat ``"app_label.codename"`` shaklidagi ruxsat kodlari
ro'yxati. ``dashboard.access_dashboard`` va boshqa maxsus kodlar
``dashboard.models.DashboardAccess`` da e'lon qilingan.
"""

# Superuser uchun alohida qator kerak emas — u har doim barcha
# ruxsatlarga ega (Django darajasida). Bu yerda faqat superuser
# bo'lmagan xodimlarga tayinlanadigan guruhlar.
ROLES = {
    "Content Manager": [
        "dashboard.access_dashboard",
        "dashboard.manage_homepage",
        "dashboard.manage_banners",
        # Filmlar va bog'liq taksonomiya — to'liq CRUD
        "movies.add_movie", "movies.change_movie", "movies.delete_movie", "movies.view_movie",
        "movies.add_genre", "movies.change_genre", "movies.delete_genre", "movies.view_genre",
        "movies.add_category", "movies.change_category", "movies.delete_category", "movies.view_category",
        "movies.add_director", "movies.change_director", "movies.delete_director", "movies.view_director",
        "movies.add_actor", "movies.change_actor", "movies.delete_actor", "movies.view_actor",
        "movies.add_country", "movies.change_country", "movies.delete_country", "movies.view_country",
        "movies.add_language", "movies.change_language", "movies.delete_language", "movies.view_language",
        "movies.add_screenshot", "movies.change_screenshot", "movies.delete_screenshot", "movies.view_screenshot",
        # Seriallar — to'liq CRUD
        "series.add_series", "series.change_series", "series.delete_series", "series.view_series",
        "series.add_season", "series.change_season", "series.delete_season", "series.view_season",
        "series.add_episode", "series.change_episode", "series.delete_episode", "series.view_episode",
        # Faqat ko'rish
        "reviews.view_review",
        "users.view_user",
        # Do'kon — mahsulotlar to'liq CRUD
        "shop.add_product", "shop.change_product", "shop.delete_product", "shop.view_product",
        "shop.view_order",
    ],
    "Moderator": [
        "dashboard.access_dashboard",
        "reviews.view_review", "reviews.change_review", "reviews.delete_review",
        "core.view_contactmessage", "core.change_contactmessage",
        "users.view_user", "users.change_user",
        "movies.view_movie",
        # Buyurtmalarni yetkazish/bekor qilish va balansni qo'lda tuzatish
        "shop.view_order", "shop.change_order",
        "dashboard.manage_balance",
    ],
    "Editor": [
        "dashboard.access_dashboard",
        "dashboard.manage_homepage",
        "dashboard.manage_banners",
        "dashboard.send_notifications",
        # Faqat tahrirlash — add/delete yo'q
        "movies.view_movie", "movies.change_movie",
        "series.view_series", "series.change_series",
        "series.view_season", "series.change_season",
        "series.view_episode", "series.change_episode",
        "movies.view_genre", "movies.view_category",
    ],
    "Analyst": [
        "dashboard.access_dashboard",
        "dashboard.view_analytics",
        "movies.view_movie", "movies.view_genre", "movies.view_category",
        "series.view_series", "series.view_season", "series.view_episode",
        "reviews.view_review",
        "users.view_user",
        "shop.view_product", "shop.view_order",
    ],
}
