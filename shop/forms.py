import re

from django import forms
from django.conf import settings

from .models import Order, Review

INDIAN_STATES = [
    "Andaman and Nicobar Islands", "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chandigarh",
    "Chhattisgarh", "Dadra and Nagar Haveli and Daman and Diu", "Delhi", "Goa", "Gujarat", "Haryana",
    "Himachal Pradesh", "Jammu and Kashmir", "Jharkhand", "Karnataka", "Kerala", "Ladakh", "Lakshadweep",
    "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Puducherry",
    "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand",
    "West Bengal",
]


def clean_indian_mobile(value):
    """Accepts 98765 43210, +91-98765-43210, 09876543210 ... and returns +919876543210."""
    digits = re.sub(r"\D", "", value or "")
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    if not re.fullmatch(r"[6-9]\d{9}", digits):
        raise forms.ValidationError("Enter a valid 10-digit Indian mobile number.")
    return "+91" + digits


class AddToCartForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, max_value=settings.MAX_QUANTITY_PER_LINE, initial=1)


class CheckoutForm(forms.ModelForm):
    state = forms.ChoiceField(choices=[("", "Select state")] + [(s, s) for s in INDIAN_STATES])

    class Meta:
        model = Order
        fields = [
            "full_name", "phone", "email", "address_line1", "address_line2",
            "city", "state", "postal_code",
        ]
        labels = {"phone": "Mobile number", "address_line1": "Address (house no., street, area)"}
        widgets = {
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "full_name": forms.TextInput(attrs={"autocomplete": "name"}),
            "phone": forms.TextInput(attrs={"autocomplete": "tel", "inputmode": "tel", "placeholder": "98765 43210"}),
            "address_line1": forms.TextInput(attrs={"autocomplete": "address-line1"}),
            "address_line2": forms.TextInput(attrs={"autocomplete": "address-line2"}),
            "city": forms.TextInput(attrs={"autocomplete": "address-level2"}),
            "postal_code": forms.TextInput(attrs={"autocomplete": "postal-code", "inputmode": "numeric", "maxlength": "6"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["phone"].required = True  # couriers need a number to reach the customer

    def clean_phone(self):
        return clean_indian_mobile(self.cleaned_data["phone"])

    def clean_postal_code(self):
        pin = re.sub(r"\s", "", self.cleaned_data["postal_code"])
        if not re.fullmatch(r"[1-9]\d{5}", pin):
            raise forms.ValidationError("Enter a valid 6-digit PIN code.")
        return pin

    def clean(self):
        cleaned = super().clean()
        cleaned["country"] = "India"
        return cleaned


class ReviewForm(forms.ModelForm):
    rating = forms.TypedChoiceField(
        choices=[(5, "5 - Loved it"), (4, "4 - Really good"), (3, "3 - It's okay"), (2, "2 - Not great"), (1, "1 - Disappointed")],
        coerce=int,
        widget=forms.RadioSelect,
    )

    class Meta:
        model = Review
        fields = ["rating", "title", "body"]
        labels = {"title": "Headline (optional)", "body": "Your review (optional)"}
        widgets = {"body": forms.Textarea(attrs={"rows": 4})}


class TrackOrderForm(forms.Form):
    order_number = forms.CharField(label="Order number", max_length=20, widget=forms.TextInput(attrs={"placeholder": "BD000123"}))
    email = forms.EmailField(label="Email used at checkout")

    def clean_order_number(self):
        digits = re.sub(r"\D", "", self.cleaned_data["order_number"])
        if not digits:
            raise forms.ValidationError("Enter the order number from your confirmation email.")
        return int(digits)
