import json
import logging
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .. import payments
from ..cart import Cart
from ..forms import CheckoutForm, TrackOrderForm
from ..models import Order
from ..services import EmptyCartError, create_order_from_cart, fulfill_order

logger = logging.getLogger(__name__)

PENDING_ORDER_SESSION_KEY = "pending_order"
CONFIRMED_STATUSES = (Order.Status.PAID, Order.Status.REVIEW, Order.Status.SHIPPED)


def clear_cart_if_order_confirmed(request):
    """
    Once the order this browser started has been confirmed paid, empty the cart.
    Called from the pages a customer is likely to visit next, so it works even if
    they closed the tab before returning from the payment page.
    """
    pending = request.session.get(PENDING_ORDER_SESSION_KEY)
    if not pending:
        return
    status = Order.objects.filter(public_id=pending).values_list("status", flat=True).first()
    if status in CONFIRMED_STATUSES:
        request.session.pop(Cart.SESSION_KEY, None)
        del request.session[PENDING_ORDER_SESSION_KEY]
    elif status in (None, Order.Status.CANCELLED):
        del request.session[PENDING_ORDER_SESSION_KEY]  # abandoned; keep the cart


def _checkout_initial(request):
    """Pre-fill the form for signed-in customers from their latest order."""
    if not request.user.is_authenticated:
        return {}
    last = request.user.orders.first()
    if last:
        return {f: getattr(last, f) for f in CheckoutForm.Meta.fields}
    return {"full_name": request.user.get_full_name(), "email": request.user.email}


def checkout(request):
    clear_cart_if_order_confirmed(request)
    cart = Cart(request)
    lines = cart.lines()
    if cart.warnings:
        for warning in cart.warnings:
            messages.warning(request, warning)
        return redirect("shop:cart")
    if not lines:
        messages.info(request, "Your cart is empty.")
        return redirect("shop:product_list")

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            try:
                order = create_order_from_cart(cart, form.cleaned_data, user=request.user)
            except EmptyCartError:
                return redirect("shop:cart")
            try:
                payment_url = payments.start_payment(order)
            except payments.PaymentError:
                logger.exception("Could not start payment for order %s", order.pk)
                order.status = Order.Status.CANCELLED
                order.save(update_fields=["status"])
                messages.error(request, "We couldn't reach the payment provider. Please try again in a moment.")
                return redirect("shop:cart")
            request.session[PENDING_ORDER_SESSION_KEY] = str(order.public_id)
            return redirect(payment_url)
    else:
        form = CheckoutForm(initial=_checkout_initial(request))

    return render(request, "shop/checkout.html", {"cart": cart, "form": form})


def order_detail(request, public_id):
    order = get_object_or_404(Order.objects.prefetch_related("items"), public_id=public_id)
    clear_cart_if_order_confirmed(request)
    # The gateway confirmation can arrive a few seconds after the customer does. Refresh briefly.
    recent = timezone.now() - order.created_at < timedelta(minutes=30)
    return render(request, "shop/order_detail.html", {
        "order": order,
        "auto_refresh": order.status == Order.Status.PENDING and recent,
    })


def track_order(request):
    """Guests can look up an order with its number and the email used at checkout."""
    form = TrackOrderForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        order = Order.objects.filter(pk=form.cleaned_data["order_number"], email__iexact=form.cleaned_data["email"]).first()
        if order:
            return redirect(order)
        messages.error(request, "We couldn't find an order with that number and email. Please check and try again.")
    return render(request, "shop/track_order.html", {"form": form})


# --- Razorpay -------------------------------------------------------------------

def pay(request, public_id):
    """Page that opens Razorpay's checkout for a pending order."""
    order = get_object_or_404(Order, public_id=public_id)
    if settings.PAYMENT_PROVIDER != "razorpay" or order.payment_provider != "razorpay":
        raise Http404
    if order.status != Order.Status.PENDING or not order.payment_reference:
        return redirect(order)
    return render(request, "shop/pay.html", {"order": order, "options": payments.checkout_options(order)})


@csrf_exempt
@require_POST
def razorpay_callback(request, public_id):
    """
    Razorpay POSTs here after a successful payment. The signature proves the payment
    belongs to this order's gateway id; nothing is trusted until it verifies.
    (CSRF-exempt because the request comes from razorpay.com, not from our own forms.)
    """
    order = get_object_or_404(Order, public_id=public_id)
    gateway_order_id = request.POST.get("razorpay_order_id", "")
    payment_id = request.POST.get("razorpay_payment_id", "")
    signature = request.POST.get("razorpay_signature", "")

    valid = (
        gateway_order_id == order.payment_reference
        and payments.verify_razorpay_payment(gateway_order_id, payment_id, signature)
    )
    if not valid:
        logger.warning("Invalid Razorpay callback signature for order %s", order.pk)
        messages.error(request, "We couldn't verify that payment. If money was deducted, it will be refunded automatically. Please try again.")
        return redirect("shop:pay", public_id=order.public_id)

    fulfill_order(order.pk, payment_reference=gateway_order_id, payment_id=payment_id)
    return redirect(order)


@csrf_exempt
@require_POST
def razorpay_webhook(request):
    """
    Backup path: covers customers who paid but closed the tab before the callback ran.
    Configure it in the Razorpay dashboard for the payment.captured and order.paid events.
    """
    if not payments.verify_razorpay_webhook(request.body, request.META.get("HTTP_X_RAZORPAY_SIGNATURE", "")):
        return HttpResponseBadRequest("Invalid signature")
    try:
        event = json.loads(request.body)
        payment = event["payload"]["payment"]["entity"]
    except (ValueError, KeyError, TypeError):
        return HttpResponse(status=200)  # not an event we handle

    if event.get("event") in ("payment.captured", "order.paid"):
        order = Order.objects.filter(payment_reference=payment.get("order_id") or "-").first()
        if order:
            fulfill_order(order.pk, payment_reference=order.payment_reference, payment_id=payment.get("id", ""))
        else:
            logger.warning("Razorpay event %s for unknown gateway order %s", event.get("event"), payment.get("order_id"))
    return HttpResponse(status=200)


# --- Development payment simulator (disabled unless PAYMENT_PROVIDER=dev) -----------

def dev_pay(request, public_id):
    # settings.py refuses to start with PAYMENT_PROVIDER=dev when DEBUG is off,
    # so this simulator can never be reached on a live site.
    if settings.PAYMENT_PROVIDER != "dev":
        raise Http404
    order = get_object_or_404(Order, public_id=public_id)

    if request.method == "POST" and order.status == Order.Status.PENDING:
        if request.POST.get("action") == "pay":
            fulfill_order(order.pk, payment_reference=f"dev-{order.public_id}", payment_id="dev-payment")
        else:
            order.status = Order.Status.CANCELLED
            order.save(update_fields=["status"])
        return redirect(order)

    return render(request, "shop/dev_pay.html", {"order": order})
