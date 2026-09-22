"""Film katalogi URL lari. SEO-friendly, slug asosida."""

from django.urls import path

from . import api, views

app_name = "movies"

urlpatterns = [
    # Filmlar ro'yxati endi umumiy katalogda (`core:catalog`) -- eski
    # havolalar filtrlari bilan birga o'sha yerga yo'naltiriladi.
    path("movies/", views.MovieListRedirectView.as_view(), name="movie_list"),
    path("genres/", views.GenreListView.as_view(), name="genre_list"),
    path("genre/<slug:slug>/", views.GenreDetailView.as_view(), name="genre_detail"),
    path("category/<slug:slug>/", views.CategoryDetailView.as_view(), name="category_detail"),
    path("director/<slug:slug>/", views.DirectorDetailView.as_view(), name="director_detail"),
    path("actor/<slug:slug>/", views.ActorDetailView.as_view(), name="actor_detail"),
    path("search/", views.SearchView.as_view(), name="search"),
    path("movie/<slug:slug>/", views.MovieDetailView.as_view(), name="movie_detail"),
    # Pleer endi film detali sahifasining o'zida (#player) — eski
    # bookmarklar uchun yo'naltirish saqlanadi.
    path("watch/<slug:slug>/", views.WatchRedirectView.as_view(), name="watch"),

    # --- AJAX endpointlar ---
    path("api/search/", views.search_suggest, name="api_search"),
    path("api/watchlist/toggle/", api.toggle_watchlist, name="api_watchlist_toggle"),
    path("api/favorite/toggle/", api.toggle_favorite, name="api_favorite_toggle"),
    path("api/progress/", api.save_progress, name="api_progress"),
]
