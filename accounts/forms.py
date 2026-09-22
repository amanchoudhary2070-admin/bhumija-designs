from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm

from shop.forms import clean_indian_mobile

User = get_user_model()


class SignupForm(forms.ModelForm):
    full_name = forms.CharField(max_length=150, label="Full name")
    phone = forms.CharField(max_length=20, required=False, label="Mobile number", widget=forms.TextInput(attrs={"placeholder": "98765 43210"}))
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput, min_length=8)
    password2 = forms.CharField(label="Confirm password", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["email"]
        widgets = {"email": forms.EmailInput(attrs={"autocomplete": "email"})}

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean_phone(self):
        value = self.cleaned_data.get("phone", "").strip()
        return clean_indian_mobile(value) if value else ""

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Passwords don't match.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["full_name"]
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={"autocomplete": "email", "autofocus": True}))
