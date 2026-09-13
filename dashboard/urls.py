"""Boshqaruv paneli URL lari. Barchasi /dashboard/ prefiksi ostida."""

from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.DashboardIndexView.as_view(), name="index"),
    path("analytics/", views.AnalyticsView.as_view(), name="analytics"),

    # --- Filmlar ---
    path("movies/", views.MovieManageListView.as_view(), name="movie_list"),
    path("movies/add/", views.MovieCreateView.as_view(), name="movie_add"),
    path("movies/<int:pk>/edit/", views.MovieUpdateView.as_view(), name="movie_edit"),
    path("movies/<int:pk>/delete/", views.MovieDeleteView.as_view(), name="movie_delete"),

    # --- Seriallar / fasllar / epizodlar ---
    path("series/", views.SeriesManageListView.as_view(), name="series_list"),
    path("series/add/", views.SeriesCreateView.as_view(), name="series_add"),
    path("series/<int:pk>/edit/", views.SeriesUpdateView.as_view(), name="series_edit"),
    path("series/<int:pk>/delete/", views.SeriesDeleteView.as_view(), name="series_delete"),
    path(
        "series/<int:series_pk>/seasons/",
        views.SeasonListView.as_view(), name="season_list",
    ),
    path(
        "series/<int:series_pk>/seasons/add/",
        views.SeasonCreateView.as_view(), name="season_add",
    ),
    path("seasons/<int:pk>/edit/", views.SeasonUpdateView.as_view(), name="season_edit"),
    path("seasons/<int:pk>/delete/", views.SeasonDeleteView.as_view(), name="season_delete"),
    path(
        "seasons/<int:season_pk>/episodes/",
        views.EpisodeListView.as_view(), name="episode_list",
    ),
    path(
        "seasons/<int:season_pk>/episodes/add/",
        views.EpisodeCreateView.as_view(), name="episode_add",
    ),
    path("episodes/<int:pk>/edit/", views.EpisodeUpdateView.as_view(), name="episode_edit"),
    path("episodes/<int:pk>/delete/", views.EpisodeDeleteView.as_view(), name="episode_delete"),

    # --- Janrlar ---
    path("genres/", views.GenreManageView.as_view(), name="genre_list"),
    path("genres/<int:pk>/edit/", views.GenreUpdateView.as_view(), name="genre_edit"),
    path("genres/<int:pk>/delete/", views.GenreDeleteView.as_view(), name="genre_delete"),

    # --- Kategoriyalar ---
    path("categories/", views.CategoryManageView.as_view(), name="category_list"),
    path("categories/<int:pk>/edit/", views.CategoryUpdateView.as_view(), name="category_edit"),
    path("categories/<int:pk>/delete/", views.CategoryDeleteView.as_view(), name="category_delete"),

    # --- Rejissyorlar ---
    path("directors/", views.DirectorManageView.as_view(), name="director_list"),
    path("directors/<int:pk>/edit/", views.DirectorUpdateView.as_view(), name="director_edit"),
    path("directors/<int:pk>/delete/", views.DirectorDeleteView.as_view(), name="director_delete"),

    # --- Aktyorlar ---
    path("actors/", views.ActorManageView.as_view(), name="actor_list"),
    path("actors/<int:pk>/edit/", views.ActorUpdateView.as_view(), name="actor_edit"),
    path("actors/<int:pk>/delete/", views.ActorDeleteView.as_view(), name="actor_delete"),

    # --- Foydalanuvchilar va moderatsiya ---
    path("users/", views.UserManageListView.as_view(), name="user_list"),
    path("reviews/", views.ReviewManageListView.as_view(), name="review_list"),
    path("messages/", views.MessageListView.as_view(), name="message_list"),

    # --- Sayt sozlamalari ---
    path("settings/", views.SiteSettingsUpdateView.as_view(), name="site_settings"),

    # --- Bannerlar ---
    path("banners/", views.BannerManageListView.as_view(), name="banner_list"),
    path("banners/add/", views.BannerCreateView.as_view(), name="banner_add"),
    path("banners/<int:pk>/edit/", views.BannerUpdateView.as_view(), name="banner_edit"),
    path("banners/<int:pk>/delete/", views.BannerDeleteView.as_view(), name="banner_delete"),

    # --- Do'kon: mahsulotlar va buyurtmalar ---
    path("shop/products/", views.ProductManageListView.as_view(), name="shop_product_list"),
    path("shop/products/add/", views.ProductCreateView.as_view(), name="shop_product_add"),
    path(
        "shop/products/<int:pk>/edit/",
        views.ProductUpdateView.as_view(), name="shop_product_edit",
    ),
    path(
        "shop/products/<int:pk>/delete/",
        views.ProductDeleteView.as_view(), name="shop_product_delete",
    ),
    path("shop/orders/", views.OrderManageListView.as_view(), name="shop_order_list"),

    # --- Obunalar: rejalar va so'rovlar ---
    path("subscriptions/plans/", views.PlanManageListView.as_view(), name="plan_list"),
    path("subscriptions/plans/add/", views.PlanCreateView.as_view(), name="plan_add"),
    path(
        "subscriptions/plans/<int:pk>/edit/",
        views.PlanUpdateView.as_view(), name="plan_edit",
    ),
    path(
        "subscriptions/plans/<int:pk>/delete/",
        views.PlanDeleteView.as_view(), name="plan_delete",
    ),
    path(
        "subscriptions/requests/",
        views.SubscriptionManageListView.as_view(), name="subscription_list",
    ),

    # --- Bosh sahifa bo'limlari ---
    path("homepage/", views.HomepageSectionListView.as_view(), name="homepage_sections"),
    path(
        "homepage/<int:pk>/edit/",
        views.HomepageSectionUpdateView.as_view(), name="homepage_section_edit",
    ),

    # --- Bildirishnomalar ---
    path("notifications/", views.NotificationListView.as_view(), name="notification_list"),
    path("notifications/add/", views.NotificationCreateView.as_view(), name="notification_add"),
    path(
        "notifications/<int:pk>/",
        views.NotificationDetailView.as_view(), name="notification_detail",
    ),

    # --- AJAX ---
    path("api/movie/<int:pk>/publish/", views.toggle_publish, name="api_toggle_publish"),
    path("api/movie/<int:pk>/featured/", views.toggle_featured, name="api_toggle_featured"),
    path("api/movie/<int:pk>/trending/", views.toggle_trending, name="api_toggle_trending"),
    path("api/series/<int:pk>/publish/", views.toggle_series_publish, name="api_toggle_series_publish"),
    path("api/episode/<int:pk>/publish/", views.toggle_episode_publish, name="api_toggle_episode_publish"),
    path("api/user/<int:pk>/block/", views.toggle_block, name="api_toggle_block"),
    path("api/user/<int:pk>/admin/", views.toggle_admin, name="api_toggle_admin"),
    path("api/user/<int:pk>/balance/", views.adjust_user_balance, name="api_adjust_balance"),
    path("api/shop/product/<int:pk>/toggle/", views.toggle_product_active, name="api_toggle_product"),
    path("api/shop/order/<int:pk>/deliver/", views.mark_order_delivered, name="api_order_deliver"),
    path("api/shop/order/<int:pk>/cancel/", views.cancel_order, name="api_order_cancel"),
    path(
        "api/movie/<int:pk>/video/",
        views.upload_movie_video, name="api_upload_movie_video",
    ),
    path("api/plan/<int:pk>/toggle/", views.toggle_plan_active, name="api_toggle_plan"),
    path(
        "api/subscription/<int:pk>/approve/",
        views.approve_subscription, name="api_subscription_approve",
    ),
    path(
        "api/subscription/<int:pk>/reject/",
        views.reject_subscription_view, name="api_subscription_reject",
    ),
    path("api/review/<int:pk>/<str:action>/", views.moderate_review, name="api_moderate_review"),
    path("api/banner/<int:pk>/toggle/", views.toggle_banner, name="api_toggle_banner"),
    path("api/homepage/<int:pk>/toggle/", views.toggle_section, name="api_toggle_section"),
    path("api/homepage/reorder/", views.reorder_sections, name="api_reorder_sections"),
]
