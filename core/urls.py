"""Sayt darajasidagi URL lar."""

from django.urls import path

from . import views
from .catalog import CatalogView

app_name = "core"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    # Kino, multfilm va seriallar uchun yagona filtrli katalog.
    path("katalog/", CatalogView.as_view(), name="catalog"),
    path("about/", views.AboutView.as_view(), name="about"),
    path("contact/", views.ContactView.as_view(), name="contact"),
    path("privacy/", views.PrivacyView.as_view(), name="privacy"),
    path("terms/", views.TermsView.as_view(), name="terms"),
]
