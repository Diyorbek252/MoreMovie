"""Dashboard formalari — film va janr tahriri."""

from django import forms
from django.forms import inlineformset_factory

from movies.models import Actor, Category, Director, Genre, Movie, MovieCast, MovieVideo
from series.models import Episode, Season, Series, SeriesCast
from shop.models import Product
from siteconfig.models import Banner, HomepageSection, Notification, SiteSettings
from subscriptions.models import Plan, PlanPrice


class MovieForm(forms.ModelForm):
    """Filmning barcha maydonlari uchun forma.

    Widget klasslari sayt design system'iga mos: `input`, `select`, `textarea`.
    """

    class Meta:
        model = Movie
        fields = [
            "title", "original_title", "slug",
            "short_description", "meta_description",
            "poster", "backdrop",
            "trailer_url", "video_url", "video_file", "download_url",
            "release_year", "release_date", "duration_minutes", "quality",
            "age_rating", "imdb_rating",
            "genres", "categories", "country", "language", "directors",
            "license_type", "license_note", "is_download_allowed",
            "is_featured", "is_trending", "is_premium", "is_published",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "input", "placeholder": "Film nomi"}),
            "original_title": forms.TextInput(
                attrs={"class": "input", "placeholder": "Original nomi (ixtiyoriy)"}
            ),
            "slug": forms.TextInput(
                attrs={"class": "input", "placeholder": "bo'sh qoldirilsa avtomatik"}
            ),
            "short_description": forms.Textarea(attrs={"class": "textarea", "rows": 3}),
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
            "release_date": forms.DateInput(attrs={"class": "input", "type": "date"}),
            "duration_minutes": forms.NumberInput(attrs={"class": "input", "min": 0}),
            "quality": forms.Select(attrs={"class": "select"}),
            "age_rating": forms.Select(attrs={"class": "select"}),
            "imdb_rating": forms.NumberInput(
                attrs={"class": "input", "step": "0.1", "min": 0, "max": 10}
            ),
            "genres": forms.CheckboxSelectMultiple(),
            "categories": forms.CheckboxSelectMultiple(),
            "country": forms.Select(attrs={"class": "select"}),
            "language": forms.Select(attrs={"class": "select"}),
            "directors": forms.CheckboxSelectMultiple(),
            "license_type": forms.Select(attrs={"class": "select"}),
            "license_note": forms.TextInput(
                attrs={"class": "input", "placeholder": "Masalan: CC BY 4.0, Blender Foundation"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slug"].required = False
        self.fields["genres"].required = True
        # Forma endi to'liq "tavsif"ni yig'maydi — shu bo'sh qolmasligi
        # uchun "qisqa tavsif" majburiy (avval shu rolni "tavsif" o'ynardi).
        self.fields["short_description"].required = True
        # Model darajasidagi yordam matni ("bo'sh bo'lsa tavsifdan olinadi")
        # bu yerda endi teskari — save() qisqa tavsifdan to'liq tavsifni
        # to'ldiradi, aksincha emas (Django admin'da esa asl matn to'g'ri).
        self.fields["short_description"].help_text = "Kartalar va hero bo'limida ko'rsatiladi."

    def clean(self):
        """Huquqiy izchillikni tekshiramiz.

        Yuklab olishga ruxsat faqat public domain yoki litsenziyalangan
        kontent uchun berilishi mumkin — bu qoida forma darajasida ham
        ushlab turiladi, model darajasidagi `can_download` bilan bir qatorda.
        Havolaning o'zi — hatto ruxsat yoqilganda ham — majburiy emas:
        admin avval ruxsatni yoqib, havolani keyinroq qo'shishi mumkin.
        """
        cleaned = super().clean()
        license_type = cleaned.get("license_type")
        download_allowed = cleaned.get("is_download_allowed")

        legal_types = {Movie.LicenseType.PUBLIC_DOMAIN, Movie.LicenseType.LICENSED}

        if download_allowed and license_type not in legal_types:
            self.add_error(
                "is_download_allowed",
                "Yuklab olishga faqat public domain yoki litsenziyalangan "
                "kontent uchun ruxsat berish mumkin.",
            )

        if license_type == Movie.LicenseType.TRAILER_ONLY and cleaned.get("video_url"):
            self.add_error(
                "video_url",
                "«Faqat treyler» tanlanganida to'liq video havolasi bo'lmasligi kerak.",
            )

        return cleaned

    def save(self, commit=True):
        """`description` endi formada yo'q — bo'sh qolib ketmasligi uchun
        (film detali va watch sahifasi shu maydonni ko'rsatadi) "qisqa
        tavsif"dan to'ldiramiz, faqat u hali bo'sh bo'lsa (masalan eski
        yozuvni tahrirlashda mavjud to'liq tavsif saqlanib qoladi).
        """
        instance = super().save(commit=False)
        if not instance.description:
            instance.description = instance.short_description
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class MovieVideoForm(forms.ModelForm):
    """Bitta sifatdagi video manbasi. Havola yoki fayldan biri bo'lishi shart."""

    class Meta:
        model = MovieVideo
        fields = ["quality", "video_url", "video_file"]
        widgets = {
            "quality": forms.Select(attrs={"class": "select"}),
            "video_url": forms.URLInput(
                attrs={"class": "input", "placeholder": "https://.../film-1080p.mp4"}
            ),
        }

    def clean(self):
        cleaned = super().clean()

        # Bo'sh qator (hech narsa kiritilmagan) — formset uni o'zi
        # e'tiborsiz qoldiradi, shuning uchun bu yerda xato bermaymiz.
        if not self.has_changed():
            return cleaned

        if self.cleaned_data.get("DELETE"):
            return cleaned

        if not cleaned.get("video_url") and not cleaned.get("video_file"):
            raise forms.ValidationError(
                "Video havolasi yoki faylini kiriting — aks holda bu sifat ochilmaydi."
            )
        return cleaned


MovieVideoFormSet = inlineformset_factory(
    Movie,
    MovieVideo,
    form=MovieVideoForm,
    extra=1,
    can_delete=True,
)


MovieCastFormSet = inlineformset_factory(
    Movie,
    MovieCast,
    fields=["actor", "character_name", "order"],
    extra=1,
    can_delete=True,
    widgets={
        "actor": forms.Select(attrs={"class": "select"}),
        "character_name": forms.TextInput(
            attrs={"class": "input", "placeholder": "Rol nomi (ixtiyoriy)"}
        ),
        "order": forms.NumberInput(attrs={"class": "input", "min": 0}),
    },
)


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


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "description", "image", "order", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input", "placeholder": "Kategoriya nomi"}),
            "description": forms.Textarea(attrs={"class": "textarea", "rows": 2}),
            "order": forms.NumberInput(attrs={"class": "input", "min": 0}),
        }


class DirectorForm(forms.ModelForm):
    class Meta:
        model = Director
        fields = ["full_name", "photo", "bio"]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "input", "placeholder": "To'liq ism"}),
            "bio": forms.Textarea(attrs={"class": "textarea", "rows": 3}),
        }


class ActorForm(forms.ModelForm):
    class Meta:
        model = Actor
        fields = ["full_name", "photo", "bio"]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "input", "placeholder": "To'liq ism"}),
            "bio": forms.Textarea(attrs={"class": "textarea", "rows": 3}),
        }


class SeriesForm(forms.ModelForm):
    """Serial ma'lumotlari. MovieForm bilan bir xil widget konventsiyasi."""

    class Meta:
        model = Series
        fields = [
            "title", "original_title", "slug",
            "short_description",
            "poster", "backdrop", "trailer_url",
            "release_year", "end_year", "imdb_rating", "age_rating", "status",
            "genres", "categories", "country", "language", "directors",
            "is_featured", "is_trending", "is_published",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "input", "placeholder": "Serial nomi"}),
            "original_title": forms.TextInput(
                attrs={"class": "input", "placeholder": "Original nomi (ixtiyoriy)"}
            ),
            "slug": forms.TextInput(
                attrs={"class": "input", "placeholder": "bo'sh qoldirilsa avtomatik"}
            ),
            "short_description": forms.Textarea(attrs={"class": "textarea", "rows": 3}),
            "trailer_url": forms.URLInput(
                attrs={"class": "input", "placeholder": "https://www.youtube.com/embed/..."}
            ),
            "release_year": forms.NumberInput(
                attrs={"class": "input", "min": 1888, "max": 2100}
            ),
            "end_year": forms.NumberInput(attrs={"class": "input", "min": 1888, "max": 2100}),
            "imdb_rating": forms.NumberInput(
                attrs={"class": "input", "step": "0.1", "min": 0, "max": 10}
            ),
            "age_rating": forms.Select(attrs={"class": "select"}),
            "status": forms.Select(attrs={"class": "select"}),
            "genres": forms.CheckboxSelectMultiple(),
            "categories": forms.CheckboxSelectMultiple(),
            "country": forms.Select(attrs={"class": "select"}),
            "language": forms.Select(attrs={"class": "select"}),
            "directors": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slug"].required = False
        self.fields["genres"].required = True
        # Forma endi to'liq "tavsif"ni yig'maydi — shu bo'sh qolmasligi
        # uchun "qisqa tavsif" majburiy (MovieForm bilan bir xil naqsh).
        self.fields["short_description"].required = True
        self.fields["short_description"].help_text = "Kartalar va serial sahifasida ko'rsatiladi."

    def clean(self):
        """end_year berilgan bo'lsa, release_year dan kichik bo'lmasligi kerak."""
        cleaned = super().clean()
        release_year = cleaned.get("release_year")
        end_year = cleaned.get("end_year")

        if release_year and end_year and end_year < release_year:
            self.add_error(
                "end_year", "Tugagan yil boshlangan yildan oldin bo'lishi mumkin emas."
            )

        return cleaned

    def save(self, commit=True):
        """`description` endi formada yo'q — bo'sh qolib ketmasligi uchun
        (serial sahifasi shu maydonni ko'rsatadi) "qisqa tavsif"dan
        to'ldiramiz, faqat u hali bo'sh bo'lsa (masalan eski yozuvni
        tahrirlashda mavjud to'liq tavsif saqlanib qoladi).
        """
        instance = super().save(commit=False)
        if not instance.description:
            instance.description = instance.short_description
        if commit:
            instance.save()
            self.save_m2m()
        return instance


SeriesCastFormSet = inlineformset_factory(
    Series,
    SeriesCast,
    fields=["actor", "character_name", "order"],
    extra=1,
    can_delete=True,
    widgets={
        "actor": forms.Select(attrs={"class": "select"}),
        "character_name": forms.TextInput(
            attrs={"class": "input", "placeholder": "Rol nomi (ixtiyoriy)"}
        ),
        "order": forms.NumberInput(attrs={"class": "input", "min": 0}),
    },
)


class SeasonForm(forms.ModelForm):
    class Meta:
        model = Season
        fields = ["number", "title", "description", "poster", "year", "is_published"]
        widgets = {
            "number": forms.NumberInput(attrs={"class": "input", "min": 1}),
            "title": forms.TextInput(
                attrs={"class": "input", "placeholder": "Ixtiyoriy — bo'sh bo'lsa '1-fasl' kabi ko'rinadi"}
            ),
            "description": forms.Textarea(attrs={"class": "textarea", "rows": 3}),
            "year": forms.NumberInput(attrs={"class": "input", "min": 1888, "max": 2100}),
        }


class EpisodeForm(forms.ModelForm):
    """Epizod formasi. MovieForm dagi kabi yuklab olish qoidasi qo'llaniladi."""

    class Meta:
        model = Episode
        fields = [
            "episode_number", "title", "description",
            "video_url", "video_file", "download_url", "is_download_allowed",
            "duration_minutes", "quality", "language", "air_date", "is_published",
        ]
        widgets = {
            "episode_number": forms.NumberInput(attrs={"class": "input", "min": 1}),
            "title": forms.TextInput(attrs={"class": "input", "placeholder": "Epizod nomi"}),
            "description": forms.Textarea(attrs={"class": "textarea", "rows": 3}),
            "video_url": forms.URLInput(
                attrs={"class": "input", "placeholder": "https://.../epizod.mp4"}
            ),
            "download_url": forms.URLInput(attrs={"class": "input"}),
            "duration_minutes": forms.NumberInput(attrs={"class": "input", "min": 0}),
            "quality": forms.Select(attrs={"class": "select"}),
            "language": forms.Select(attrs={"class": "select"}),
            "air_date": forms.DateInput(attrs={"class": "input", "type": "date"}),
        }

    def clean(self):
        """Yuklab olish uchun havola talab qilinadi — MovieForm bilan bir xil qoida."""
        cleaned = super().clean()
        if cleaned.get("is_download_allowed") and not cleaned.get("download_url"):
            self.add_error("download_url", "Yuklab olish uchun havola kiriting.")
        return cleaned


class SiteSettingsForm(forms.ModelForm):
    """Yagona qatorli global sozlamalar formasi."""

    class Meta:
        model = SiteSettings
        fields = [
            "site_name", "logo", "favicon", "site_description",
            "contact_email", "telegram", "youtube", "instagram", "facebook",
            "copyright_text",
            "seo_title", "seo_description", "seo_keywords", "google_analytics_id",
            "maintenance_mode", "maintenance_message",
            "payment_card_number", "payment_card_holder", "payment_instructions",
        ]
        widgets = {
            "site_name": forms.TextInput(attrs={"class": "input"}),
            "site_description": forms.Textarea(attrs={"class": "textarea", "rows": 3}),
            "contact_email": forms.EmailInput(attrs={"class": "input"}),
            "telegram": forms.URLInput(attrs={"class": "input", "placeholder": "https://t.me/..."}),
            "youtube": forms.URLInput(attrs={"class": "input", "placeholder": "https://youtube.com/..."}),
            "instagram": forms.URLInput(attrs={"class": "input", "placeholder": "https://instagram.com/..."}),
            "facebook": forms.URLInput(attrs={"class": "input", "placeholder": "https://facebook.com/..."}),
            "copyright_text": forms.TextInput(
                attrs={"class": "input", "placeholder": "© 2026 MORE-MOVIE. Barcha huquqlar himoyalangan."}
            ),
            "seo_title": forms.TextInput(attrs={"class": "input", "maxlength": 70}),
            "seo_description": forms.TextInput(attrs={"class": "input", "maxlength": 170}),
            "seo_keywords": forms.TextInput(
                attrs={"class": "input", "placeholder": "kino, film, uzbek tilida"}
            ),
            "google_analytics_id": forms.TextInput(
                attrs={"class": "input", "placeholder": "G-XXXXXXXXXX"}
            ),
            "maintenance_message": forms.Textarea(
                attrs={"class": "textarea", "rows": 3,
                       "placeholder": "Sayt texnik xizmat ko'rsatish tufayli vaqtincha yopiq."}
            ),
            "payment_card_number": forms.TextInput(
                attrs={"class": "input", "placeholder": "8600 1234 5678 9012"}
            ),
            "payment_card_holder": forms.TextInput(
                attrs={"class": "input", "placeholder": "IZDANOV IZDAN"}
            ),
            "payment_instructions": forms.Textarea(
                attrs={"class": "textarea", "rows": 3,
                       "placeholder": "O'tkazmadan so'ng chek skrinshotini yuklang."}
            ),
        }


class BannerForm(forms.ModelForm):
    class Meta:
        model = Banner
        fields = [
            "title", "image", "link", "position",
            "start_date", "end_date", "is_active", "order",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "input", "placeholder": "Banner sarlavhasi"}),
            "link": forms.URLInput(attrs={"class": "input", "placeholder": "https://..."}),
            "position": forms.Select(attrs={"class": "select"}),
            "start_date": forms.DateTimeInput(attrs={"class": "input", "type": "datetime-local"}),
            "end_date": forms.DateTimeInput(attrs={"class": "input", "type": "datetime-local"}),
            "order": forms.NumberInput(attrs={"class": "input", "min": 0}),
        }

    def clean(self):
        """Sana oralig'i noto'g'ri bo'lsa bazadagi CheckConstraint'gacha
        yetib bormasdan, foydalanuvchiga tushunarli xato ko'rsatamiz."""
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")
        if start and end and end <= start:
            self.add_error("end_date", "Tugash sanasi boshlanish sanasidan keyin bo'lishi kerak.")
        return cleaned


class HomepageSectionForm(forms.ModelForm):
    """Bosh sahifa bo'limining sarlavhasi va parametrlarini tahrirlash.

    ``key`` formada YO'Q — bo'lim turi (Trending, Top Rated va h.k.)
    yaratilgandan keyin o'zgarmaydi, faqat ``seed_homepage_sections``
    orqali belgilanadi. Tartib alohida drag-and-drop AJAX orqali
    boshqariladi (``reorder_sections``), shu sabab ``order`` ham bu
    yerda yo'q.
    """

    class Meta:
        model = HomepageSection
        fields = ["title", "subtitle", "item_limit", "is_active", "category", "movie"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "input"}),
            "subtitle": forms.TextInput(attrs={"class": "input"}),
            "item_limit": forms.NumberInput(attrs={"class": "input", "min": 1, "max": 50}),
            "category": forms.Select(attrs={"class": "select"}),
            "movie": forms.Select(attrs={"class": "select"}),
        }


class NotificationForm(forms.ModelForm):
    """Bildirishnoma yaratish formasi.

    ``target_users`` faqat qamrov "Tanlangan foydalanuvchilar" bo'lganda
    ma'noga ega -- boshqa holatlarda forma darajasida talab qilinmaydi,
    ``Notification.resolve_recipients()`` uni e'tiborsiz qoldiradi.
    """

    class Meta:
        model = Notification
        fields = [
            "title", "message", "image", "notification_type",
            "link", "target", "target_users",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "input", "placeholder": "Bildirishnoma sarlavhasi"}),
            "message": forms.Textarea(attrs={"class": "textarea", "rows": 4}),
            "notification_type": forms.Select(attrs={"class": "select"}),
            "link": forms.URLInput(attrs={"class": "input", "placeholder": "https://..."}),
            "target": forms.Select(attrs={"class": "select"}),
            "target_users": forms.SelectMultiple(attrs={"class": "select", "size": 8}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["target_users"].required = False

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("target") == Notification.Target.SELECTED and not cleaned.get("target_users"):
            self.add_error(
                "target_users",
                "«Tanlangan foydalanuvchilar» qamrovi uchun kamida bitta foydalanuvchi tanlang.",
            )
        return cleaned


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "description", "image", "price", "stock", "is_active", "order"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input", "placeholder": "Mahsulot nomi"}),
            "description": forms.Textarea(attrs={"class": "textarea", "rows": 3}),
            "price": forms.NumberInput(attrs={"class": "input", "min": 1}),
            "stock": forms.NumberInput(
                attrs={"class": "input", "min": 0, "placeholder": "Bo'sh — cheksiz"}
            ),
            "order": forms.NumberInput(attrs={"class": "input", "min": 0}),
        }


class PlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = [
            "name", "tagline", "description", "features", "level",
            "allows_premium_movies", "has_badge", "is_ad_free",
            "is_highlighted", "is_active", "order",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input", "placeholder": "Masalan: Premium"}),
            "tagline": forms.TextInput(
                attrs={"class": "input", "placeholder": "Eng ommabop tanlov"}
            ),
            "description": forms.Textarea(attrs={"class": "textarea", "rows": 3}),
            "features": forms.Textarea(
                attrs={
                    "class": "textarea", "rows": 5,
                    "placeholder": "Har qatorda bitta imkoniyat\nPremium filmlar\nReklamasiz",
                }
            ),
            "level": forms.NumberInput(attrs={"class": "input", "min": 0}),
            "order": forms.NumberInput(attrs={"class": "input", "min": 0}),
        }


class PlanPriceForm(forms.ModelForm):
    class Meta:
        model = PlanPrice
        fields = ["label", "duration_days", "price", "old_price", "is_active", "order"]
        widgets = {
            "label": forms.TextInput(attrs={"class": "input", "placeholder": "1 oy"}),
            "duration_days": forms.NumberInput(attrs={"class": "input", "min": 1}),
            "price": forms.NumberInput(attrs={"class": "input", "min": 1}),
            "old_price": forms.NumberInput(
                attrs={"class": "input", "min": 1, "placeholder": "Ixtiyoriy"}
            ),
            "order": forms.NumberInput(attrs={"class": "input", "min": 0}),
        }


PlanPriceFormSet = inlineformset_factory(
    Plan,
    PlanPrice,
    form=PlanPriceForm,
    extra=1,
    can_delete=True,
)


class BalanceAdjustForm(forms.Form):
    """Foydalanuvchi balansini qo'lda tuzatish — user_list.html dagi modal orqali."""

    amount = forms.IntegerField(
        label="Miqdor",
        widget=forms.NumberInput(
            attrs={"class": "input", "placeholder": "Masalan: 50 yoki -20"}
        ),
        help_text="Musbat son qo'shadi, manfiy son ayiradi.",
    )
    note = forms.CharField(
        label="Izoh",
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "Ixtiyoriy izoh"}),
    )

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount == 0:
            raise forms.ValidationError("Miqdor 0 bo'lishi mumkin emas.")
        return amount
