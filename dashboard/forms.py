"""Dashboard formalari — film va janr tahriri."""

from django import forms

from movies.models import Genre, Movie


class MovieForm(forms.ModelForm):
    """Filmning barcha maydonlari uchun forma.

    Widget klasslari sayt design system'iga mos: `input`, `select`, `textarea`.
    """

    class Meta:
        model = Movie
        fields = [
            "title", "original_title", "slug",
            "description", "short_description", "meta_description",
            "poster", "backdrop",
            "trailer_url", "video_url", "video_file", "download_url",
            "release_year", "duration_minutes", "quality", "imdb_rating",
            "genres", "country", "language", "director",
            "license_type", "license_note", "is_download_allowed",
            "is_featured", "is_published",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "input", "placeholder": "Film nomi"}),
            "original_title": forms.TextInput(
                attrs={"class": "input", "placeholder": "Original nomi (ixtiyoriy)"}
            ),
            "slug": forms.TextInput(
                attrs={"class": "input", "placeholder": "bo'sh qoldirilsa avtomatik"}
            ),
            "description": forms.Textarea(attrs={"class": "textarea", "rows": 6}),
            "short_description": forms.Textarea(attrs={"class": "textarea", "rows": 2}),
            "meta_description": forms.TextInput(
                attrs={"class": "input", "maxlength": 170, "placeholder": "SEO tavsifi"}
            ),
            "trailer_url": forms.URLInput(
                attrs={"class": "input", "placeholder": "https://www.youtube.com/embed/..."}
            ),
            "video_url": forms.URLInput(
                attrs={"class": "input", "placeholder": "https://.../film.mp4"}
            ),
            "download_url": forms.URLInput(attrs={"class": "input"}),
            "release_year": forms.NumberInput(
                attrs={"class": "input", "min": 1888, "max": 2100}
            ),
            "duration_minutes": forms.NumberInput(attrs={"class": "input", "min": 0}),
            "quality": forms.Select(attrs={"class": "select"}),
            "imdb_rating": forms.NumberInput(
                attrs={"class": "input", "step": "0.1", "min": 0, "max": 10}
            ),
            "genres": forms.CheckboxSelectMultiple(),
            "country": forms.Select(attrs={"class": "select"}),
            "language": forms.Select(attrs={"class": "select"}),
            "director": forms.Select(attrs={"class": "select"}),
            "license_type": forms.Select(attrs={"class": "select"}),
            "license_note": forms.TextInput(
                attrs={"class": "input", "placeholder": "Masalan: CC BY 4.0, Blender Foundation"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slug"].required = False
        self.fields["genres"].required = True

    def clean(self):
        """Huquqiy izchillikni tekshiramiz.

        Yuklab olishga ruxsat faqat public domain yoki litsenziyalangan
        kontent uchun berilishi mumkin — bu qoida forma darajasida ham
        ushlab turiladi, model darajasidagi `can_download` bilan bir qatorda.
        """
        cleaned = super().clean()
        license_type = cleaned.get("license_type")
        download_allowed = cleaned.get("is_download_allowed")
        download_url = cleaned.get("download_url")

        legal_types = {Movie.LicenseType.PUBLIC_DOMAIN, Movie.LicenseType.LICENSED}

        if download_allowed and license_type not in legal_types:
            self.add_error(
                "is_download_allowed",
                "Yuklab olishga faqat public domain yoki litsenziyalangan "
                "kontent uchun ruxsat berish mumkin.",
            )

        if download_allowed and not download_url:
            self.add_error("download_url", "Yuklab olish uchun havola kiriting.")

        if license_type == Movie.LicenseType.TRAILER_ONLY and cleaned.get("video_url"):
            self.add_error(
                "video_url",
                "«Faqat treyler» tanlanganida to'liq video havolasi bo'lmasligi kerak.",
            )

        return cleaned


class GenreForm(forms.ModelForm):
    class Meta:
        model = Genre
        fields = ["name", "icon", "order", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input", "placeholder": "Janr nomi"}),
            "icon": forms.TextInput(attrs={"class": "input", "placeholder": "ikonka kaliti"}),
            "order": forms.NumberInput(attrs={"class": "input", "min": 0}),
            "description": forms.Textarea(attrs={"class": "textarea", "rows": 2}),
        }
