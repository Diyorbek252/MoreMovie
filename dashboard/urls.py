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
    path("api/user/<int:pk>/block/", views.toggle_block, name="api_toggle_block"),
    path("api/review/<int:pk>/<str:action>/", views.moderate_review, name="api_moderate_review"),
]
