"""Foydalanuvchi formalari: ro'yxatdan o'tish, kirish, profil tahriri."""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Profile

User = get_user_model()


class RegisterForm(UserCreationForm):
    """Ro'yxatdan o'tish formasi — email majburiy va unikal."""

    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={"class": "input", "placeholder": "email@misol.uz", "autocomplete": "email"}
        ),
    )

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]
        widgets = {
            "username": forms.TextInput(
                attrs={
                    "class": "input",
                    "placeholder": "foydalanuvchi_nomi",
                    "autocomplete": "username",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # UserCreationForm parol maydonlarini dinamik yaratadi, shuning uchun
        # ularning widget atributlarini shu yerda beramiz.
        self.fields["password1"].widget.attrs.update(
            {"class": "input", "placeholder": "Kamida 8 ta belgi", "autocomplete": "new-password"}
        )
        self.fields["password2"].widget.attrs.update(
            {"class": "input", "placeholder": "Parolni takrorlang", "autocomplete": "new-password"}
        )
        self.fields["username"].label = "Foydalanuvchi nomi"
        self.fields["password1"].label = "Parol"
        self.fields["password2"].label = "Parolni tasdiqlang"
        self.fields["username"].help_text = "Harflar, raqamlar va @ . + - _ belgilari."

    def clean_email(self):
        """Email takrorlanmasligini tekshiramiz (katta/kichik harfdan qat'i nazar)."""
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Bu email allaqachon ro'yxatdan o'tgan.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    """Kirish formasi — username yoki email, hamda "Remember me"."""

    username = forms.CharField(
        label="Username yoki email",
        widget=forms.TextInput(
            attrs={
                "class": "input",
                "placeholder": "username yoki email@misol.uz",
                "autocomplete": "username",
                "autofocus": True,
            }
        ),
    )
    password = forms.CharField(
        label="Parol",
        widget=forms.PasswordInput(
            attrs={
                "class": "input",
                "placeholder": "Parolingiz",
                "autocomplete": "current-password",
            }
        ),
    )
    remember_me = forms.BooleanField(
        label="Meni eslab qol",
        required=False,
        initial=True,
    )

    # Xato xabarlarini o'zbekchalashtiramiz.
    error_messages = {
        "invalid_login": "Username/email yoki parol noto'g'ri.",
        "inactive": "Bu hisob faol emas.",
    }


class ProfileForm(forms.ModelForm):
    """Profil ma'lumotlarini tahrirlash."""

    class Meta:
        model = Profile
        fields = ["avatar", "bio", "country"]
        widgets = {
            "bio": forms.Textarea(
                attrs={"class": "textarea", "rows": 4, "placeholder": "O'zingiz haqingizda..."}
            ),
            "country": forms.TextInput(
                attrs={"class": "input", "placeholder": "Masalan: O'zbekiston"}
            ),
        }
        labels = {"avatar": "Avatar", "bio": "Bio", "country": "Davlat"}


class UserForm(forms.ModelForm):
    """User modelidagi asosiy maydonlar (profil tahriri bilan birga ishlatiladi)."""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "input", "placeholder": "Ism"}),
            "last_name": forms.TextInput(attrs={"class": "input", "placeholder": "Familiya"}),
            "email": forms.EmailInput(attrs={"class": "input"}),
        }
        labels = {"first_name": "Ism", "last_name": "Familiya", "email": "Email"}

    def clean_email(self):
        """Email boshqa foydalanuvchida band emasligini tekshiramiz."""
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Bu email boshqa hisobga biriktirilgan.")
        return email
