"""Film katalogi URL lari. SEO-friendly, slug asosida."""

from django.urls import path

from . import api, views

app_name = "movies"

urlpatterns = [
    path("movies/", views.MovieListView.as_view(), name="movie_list"),
    path("genres/", views.GenreListView.as_view(), name="genre_list"),
    path("genre/<slug:slug>/", views.GenreDetailView.as_view(), name="genre_detail"),
    path("search/", views.SearchView.as_view(), name="search"),
    path("movie/<slug:slug>/", views.MovieDetailView.as_view(), name="movie_detail"),
    path("watch/<slug:slug>/", views.WatchView.as_view(), name="watch"),

    # --- AJAX endpointlar ---
    path("api/search/", views.search_suggest, name="api_search"),
    path("api/watchlist/toggle/", api.toggle_watchlist, name="api_watchlist_toggle"),
    path("api/favorite/toggle/", api.toggle_favorite, name="api_favorite_toggle"),
    path("api/progress/", api.save_progress, name="api_progress"),
]
