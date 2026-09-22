from django import forms

from shop.forms import clean_indian_mobile

from .models import ContactMessage, CustomArtRequest, Subscriber


class NewsletterForm(forms.ModelForm):
    class Meta:
        model = Subscriber
        fields = ["email"]
        widgets = {"email": forms.EmailInput(attrs={"placeholder": "Enter your email address"})}

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "subject", "message"]
        widgets = {"message": forms.Textarea(attrs={"rows": 5})}


class CustomArtRequestForm(forms.ModelForm):
    class Meta:
        model = CustomArtRequest
        fields = ["name", "email", "phone", "description", "size", "budget", "reference_image"]
        labels = {"phone": "Mobile number (optional)"}
        widgets = {"description": forms.Textarea(attrs={"rows": 5, "placeholder": "Style, subject, colours, where it will go..."})}

    def clean_phone(self):
        value = self.cleaned_data.get("phone", "").strip()
        return clean_indian_mobile(value) if value else ""
