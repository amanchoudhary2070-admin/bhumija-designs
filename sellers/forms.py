from django import forms

from shop.forms import clean_indian_mobile
from shop.models import Category, Product, SellerProfile


class SellerApplicationForm(forms.ModelForm):
    class Meta:
        model = SellerProfile
        fields = ["shop_name", "phone", "bio", "logo"]
        labels = {"shop_name": "Your shop / brand name", "bio": "Tell buyers about your work"}
        widgets = {"bio": forms.Textarea(attrs={"rows": 4, "placeholder": "What do you make, and how?"})}

    def clean_phone(self):
        value = self.cleaned_data.get("phone", "").strip()
        return clean_indian_mobile(value) if value else ""


class SellerProductForm(forms.ModelForm):
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Categories",
    )

    class Meta:
        model = Product
        fields = [
            "name", "categories", "description", "details", "price", "compare_at_price",
            "stock", "image", "dimensions", "materials", "dispatch_days",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "details": forms.TextInput(attrs={"placeholder": "Short line under the name, e.g. size or material"}),
        }

    def clean(self):
        cleaned = super().clean()
        price, compare = cleaned.get("price"), cleaned.get("compare_at_price")
        if price and compare and compare <= price:
            self.add_error("compare_at_price", "MRP must be higher than the selling price, or leave it empty.")
        return cleaned
