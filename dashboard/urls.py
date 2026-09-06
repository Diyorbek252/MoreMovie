"""Boshqaruv paneli URL lari. Barchasi /dashboard/ prefiksi ostida."""

from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.DashboardIndexView.as_view(), name="index"),

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

    # --- Foydalanuvchilar va moderatsiya ---
    path("users/", views.UserManageListView.as_view(), name="user_list"),
    path("reviews/", views.ReviewManageListView.as_view(), name="review_list"),
    path("messages/", views.MessageListView.as_view(), name="message_list"),

    # --- AJAX ---
    path("api/movie/<int:pk>/publish/", views.toggle_publish, name="api_toggle_publish"),
    path("api/movie/<int:pk>/featured/", views.toggle_featured, name="api_toggle_featured"),
    path("api/movie/<int:pk>/trending/", views.toggle_trending, name="api_toggle_trending"),
    path("api/series/<int:pk>/publish/", views.toggle_series_publish, name="api_toggle_series_publish"),
    path("api/episode/<int:pk>/publish/", views.toggle_episode_publish, name="api_toggle_episode_publish"),
    path("api/user/<int:pk>/block/", views.toggle_block, name="api_toggle_block"),
    path("api/review/<int:pk>/<str:action>/", views.moderate_review, name="api_moderate_review"),
]
