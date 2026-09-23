from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from shop.models import OrderItem, Product, SellerProfile

from .forms import SellerApplicationForm, SellerProductForm


def _seller_or_none(user):
    return getattr(user, "seller_profile", None) if user.is_authenticated else None


@login_required
def apply(request):
    existing = _seller_or_none(request.user)
    if existing:
        return redirect("sellers:dashboard")

    if request.method == "POST":
        form = SellerApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            seller = form.save(commit=False)
            seller.user = request.user
            seller.save()
            messages.success(
                request,
                "Thanks! Your seller application is in. We review new sellers within a couple of "
                "working days — you'll be able to add products as soon as you're approved.",
            )
            return redirect("sellers:dashboard")
    else:
        form = SellerApplicationForm()
    return render(request, "sellers/apply.html", {"form": form})


@login_required
def dashboard(request):
    seller = _seller_or_none(request.user)
    if not seller:
        return redirect("sellers:apply")
    products = seller.products.all()
    pending_orders = OrderItem.objects.filter(seller=seller, order__status__in=["paid", "shipped"]).count()
    return render(request, "sellers/dashboard.html", {
        "seller": seller,
        "product_count": products.count(),
        "active_count": products.filter(is_active=True).count(),
        "pending_orders": pending_orders,
        "recent_products": products[:5],
    })


@login_required
def product_list(request):
    seller = _seller_or_none(request.user)
    if not seller:
        return redirect("sellers:apply")
    page = Paginator(seller.products.all(), 15).get_page(request.GET.get("page"))
    return render(request, "sellers/product_list.html", {"seller": seller, "page": page})


@login_required
def product_create(request):
    seller = _seller_or_none(request.user)
    if not seller:
        return redirect("sellers:apply")
    if not seller.is_approved:
        messages.info(request, "Your seller account is still awaiting approval, so new listings aren't public yet — but you can prepare them now.")

    if request.method == "POST":
        form = SellerProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = seller
            product.save()
            form.save_m2m()
            messages.success(request, f"“{product.name}” has been added.")
            return redirect("sellers:product_list")
    else:
        form = SellerProductForm()
    return render(request, "sellers/product_form.html", {"form": form, "seller": seller, "is_new": True})


@login_required
def product_edit(request, pk):
    seller = _seller_or_none(request.user)
    if not seller:
        return redirect("sellers:apply")
    # get_object_or_404 scoped to this seller's own products: a seller can never edit
    # another seller's listing, even by guessing a product id in the URL.
    product = get_object_or_404(Product, pk=pk, seller=seller)

    if request.method == "POST":
        form = SellerProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f"“{product.name}” has been updated.")
            return redirect("sellers:product_list")
    else:
        form = SellerProductForm(instance=product)
    return render(request, "sellers/product_form.html", {"form": form, "seller": seller, "is_new": False, "product": product})


@require_POST
@login_required
def product_toggle_active(request, pk):
    seller = _seller_or_none(request.user)
    if not seller:
        return redirect("sellers:apply")
    product = get_object_or_404(Product, pk=pk, seller=seller)
    product.is_active = not product.is_active
    product.save(update_fields=["is_active"])
    messages.success(request, f"“{product.name}” is now {'visible' if product.is_active else 'hidden'} in the shop.")
    return redirect("sellers:product_list")


@login_required
def order_list(request):
    seller = _seller_or_none(request.user)
    if not seller:
        return redirect("sellers:apply")
    # Only items from paid/shipped orders, and only this seller's own line items —
    # a seller never sees another seller's items or a buyer's full order contents.
    items = (
        OrderItem.objects.filter(seller=seller, order__status__in=["paid", "shipped"])
        .select_related("order")
        .order_by("-order__created_at")
    )
    page = Paginator(items, 20).get_page(request.GET.get("page"))
    return render(request, "sellers/order_list.html", {"seller": seller, "page": page})


@require_POST
@login_required
def order_item_toggle_shipped(request, pk):
    seller = _seller_or_none(request.user)
    if not seller:
        return redirect("sellers:apply")
    item = get_object_or_404(OrderItem, pk=pk, seller=seller)
    item.is_shipped_by_seller = not item.is_shipped_by_seller
    item.save(update_fields=["is_shipped_by_seller"])
    return redirect("sellers:order_list")
