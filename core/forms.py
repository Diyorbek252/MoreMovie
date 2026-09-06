"""Sayt darajasidagi formalar."""

from django import forms

from .models import ContactMessage


class ContactForm(forms.ModelForm):
    """Contact sahifasidagi murojaat formasi.

    Widget atributlari shu yerda beriladi, shablonda esa `{{ form.field }}`
    to'g'ridan-to'g'ri chiziladi — bu HTML ni toza saqlaydi.
    """

    class Meta:
        model = ContactMessage
        fields = ["name", "email", "subject", "message"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "input", "placeholder": "Ismingiz", "autocomplete": "name"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "input", "placeholder": "email@misol.uz", "autocomplete": "email"}
            ),
            "subject": forms.TextInput(
                attrs={"class": "input", "placeholder": "Murojaat mavzusi"}
            ),
            "message": forms.Textarea(
                attrs={"class": "textarea", "placeholder": "Xabaringizni yozing...", "rows": 6}
            ),
        }

    def clean_message(self):
        message = self.cleaned_data["message"].strip()
        if len(message) < 10:
            raise forms.ValidationError("Xabar kamida 10 ta belgidan iborat bo'lishi kerak.")
        return message
