from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from ..cart import Cart
from ..forms import AddToCartForm
from ..models import Product
from .checkout import clear_cart_if_order_confirmed


def cart_detail(request):
    clear_cart_if_order_confirmed(request)
    cart = Cart(request)
    cart.lines()  # reconcile with the database before showing anything
    for warning in cart.warnings:
        messages.warning(request, warning)
    return render(request, "shop/cart.html", {"cart": cart})


@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    form = AddToCartForm(request.POST)
    if not product.in_stock:
        messages.error(request, f"“{product.name}” has sold out.")
        return redirect(product)
    if not form.is_valid():
        messages.error(request, "Choose a quantity between 1 and %d." % settings.MAX_QUANTITY_PER_LINE)
        return redirect(product)

    cart = Cart(request)
    before = len(cart)
    cart.add(product, form.cleaned_data["quantity"])
    if request.POST.get("buy_now"):
        return redirect("shop:checkout")
    if len(cart) == before:
        messages.info(request, f"You already have every available “{product.name}” in your cart.")
    else:
        messages.success(request, f"Added “{product.name}” to your cart.")
    return redirect("shop:cart")


@require_POST
def cart_update(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    try:
        quantity = int(request.POST.get("quantity", 1))
    except ValueError:
        quantity = 1
    Cart(request).add(product, max(quantity, 0), replace=True)
    return redirect("shop:cart")


@require_POST
def cart_remove(request, product_id):
    Cart(request).remove(product_id)
    return redirect("shop:cart")
