"""DRF serializerlari — murojaat formasi."""

from users.serializers import FormBackedSerializer

from .forms import ContactForm


class ContactSerializer(FormBackedSerializer):
    """`POST /api/v1/contact/` — mavjud `ContactForm` validatsiyasidan foydalanadi."""

    form_class = ContactForm

    def save(self, **kwargs):
        return self._form.save()
