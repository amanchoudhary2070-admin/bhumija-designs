from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from shop.models import Order, WishlistItem

from .forms import EmailAuthenticationForm, SignupForm

User = get_user_model()


class LoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True


class SignupView(CreateView):
    form_class = SignupForm
    template_name = "accounts/signup.html"
    success_url = reverse_lazy("accounts:dashboard")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object, backend="django.contrib.auth.backends.ModelBackend")
        messages.success(self.request, f"Welcome to {self.request.session.get('shop_name', '')}!".strip() or "Welcome!")
        return response


@login_required
def dashboard(request):
    orders = request.user.orders.all()[:5]
    wishlist_count = WishlistItem.objects.filter(user=request.user).count()
    return render(request, "accounts/dashboard.html", {"orders": orders, "wishlist_count": wishlist_count})


@login_required
def order_history(request):
    orders = request.user.orders.prefetch_related("items")
    return render(request, "accounts/orders.html", {"orders": orders})


@login_required
def profile(request):
    user = request.user
    if request.method == "POST":
        user.first_name = request.POST.get("full_name", user.first_name).strip()[:150]
        user.save(update_fields=["first_name"])
        messages.success(request, "Your details have been updated.")
        return redirect("accounts:profile")
    return render(request, "accounts/profile.html")
