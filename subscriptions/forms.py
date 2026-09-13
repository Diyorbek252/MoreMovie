"""Public forma — obuna so'rovi yuborish."""

from django import forms

from .models import Subscription


class SubscriptionRequestForm(forms.ModelForm):
    """Foydalanuvchi to'lov qilgach shu formani to'ldiradi.

    `plan`/`price` maydonlari bu yerda YO'Q — ular view'da URL/POST
    parametrlaridan olinib, snapshot sifatida `save()`dan oldin
    o'rnatiladi (qarang: SubscriptionRequestView).
    """

    class Meta:
        model = Subscription
        fields = ["payment_note", "payment_receipt"]
        widgets = {
            "payment_note": forms.TextInput(
                attrs={
                    "class": "input",
                    "placeholder": "Masalan: karta ...1234 dan, 14:30 da o'tkazildi",
                }
            ),
            "payment_receipt": forms.ClearableFileInput(attrs={"class": "input"}),
        }
        labels = {
            "payment_note": "To'lov haqida qisqacha",
            "payment_receipt": "To'lov cheki (skrinshot)",
        }
