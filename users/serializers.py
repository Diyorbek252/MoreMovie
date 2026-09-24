"""DRF serializerlari — autentifikatsiya va profil.

Mavjud `RegisterForm`/`LoginForm`/`UserForm`/`ProfileForm` (`users/forms.py`)
qayta yozilmaydi — validatsiya mantig'i (email unikal, parol qoidalari,
"remember me") shu formalarning o'zidan foydalanadi, faqat DRF qatlami
ularni JSON so'rov/javobga o'raydi.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .forms import LoginForm, ProfileForm, RegisterForm, UserForm
from .models import Profile

User = get_user_model()


class ProfileSerializer(serializers.ModelSerializer):
    avatar_url = serializers.ReadOnlyField()

    class Meta:
        model = Profile
        fields = ["avatar_url", "bio", "country", "show_continue_watching", "balance"]
        read_only_fields = ["balance"]


class UserSerializer(serializers.ModelSerializer):
    """`GET /api/v1/auth/me/` javobi."""

    display_name = serializers.ReadOnlyField()
    initials = serializers.ReadOnlyField()
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name",
            "display_name", "initials", "is_staff", "profile",
        ]


class FormBackedSerializer(serializers.Serializer):
    """Django `Form`ga tayanadigan DRF serializer — validatsiya xatolarini
    forma o'zidan oladi, ikki marta yozilmaydi.

    Subklass `form_class` ni belgilashi va `save()` ni implement qilishi
    kerak; `is_valid()` ichida forma ham to'ldiriladi (`self._form`).
    """

    form_class = None
    form_kwargs = {}

    def to_internal_value(self, data):
        self._form = self.form_class(data=data, **self.form_kwargs)
        if not self._form.is_valid():
            # Django forma xatolarini DRF formatiga o'giramiz:
            # {"field": ["xabar", ...], "non_field_errors": [...]}
            raise serializers.ValidationError(self._form.errors)
        return self._form.cleaned_data


class RegisterSerializer(FormBackedSerializer):
    form_class = RegisterForm

    def save(self, **kwargs):
        return self._form.save()


class LoginSerializer(FormBackedSerializer):
    """`LoginForm` — `AuthenticationForm` avlodi, `request` talab qiladi."""

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        self._form = LoginForm(data=data, request=self.request)
        if not self._form.is_valid():
            raise serializers.ValidationError(self._form.errors)
        return self._form.cleaned_data

    @property
    def user(self):
        return self._form.get_user()

    @property
    def remember_me(self):
        return self._form.cleaned_data.get("remember_me")


class ProfileUpdateSerializer(serializers.Serializer):
    """`PATCH /api/v1/me/profile/` — `UserForm` + `ProfileForm` birga
    saqlanadi (`users/views.py::profile_edit` bilan bir xil mantiq)."""

    def __init__(self, *args, **kwargs):
        self.user_instance = kwargs.pop("instance")
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        self._user_form = UserForm(data=data, instance=self.user_instance)
        self._profile_form = ProfileForm(
            data=data, files=self.context["request"].FILES or None,
            instance=self.user_instance.profile,
        )
        user_valid = self._user_form.is_valid()
        profile_valid = self._profile_form.is_valid()
        if not (user_valid and profile_valid):
            errors = {**self._user_form.errors, **self._profile_form.errors}
            raise serializers.ValidationError(errors)
        return {}

    def save(self, **kwargs):
        self._user_form.save()
        self._profile_form.save()
        return self.user_instance
