"""
Payment providers.

start_payment() returns a URL to send the customer to. Whatever the provider, the
order is only marked paid by services.fulfill_order(), and only after a payment
signature has been verified on the server (Razorpay's signed callback or its signed
webhook), or by the dev simulator. A customer merely visiting a "success" URL never
marks anything paid.

Razorpay is called over plain HTTPS (no SDK needed). To add another gateway, write a
function shaped like _create_razorpay_order plus a verified callback/webhook view that
ends in fulfill_order().
"""
import hashlib
import hmac
from decimal import Decimal

import requests
from django.conf import settings
from django.urls import reverse

RAZORPAY_ORDERS_URL = "https://api.razorpay.com/v1/orders"


class PaymentError(Exception):
    """Raised when the payment provider can't start a checkout."""


def to_paise(amount):
    return int((Decimal(amount) * 100).to_integral_value())


def start_payment(order):
    if settings.PAYMENT_PROVIDER == "razorpay":
        _create_razorpay_order(order)
        return reverse("shop:pay", args=[order.public_id])
    if settings.PAYMENT_PROVIDER == "dev":
        return reverse("shop:dev_pay", args=[order.public_id])
    raise PaymentError(f"Unknown PAYMENT_PROVIDER: {settings.PAYMENT_PROVIDER!r}")


def _create_razorpay_order(order):
    if not (settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET):
        raise PaymentError("Razorpay is not configured (RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET missing).")
    try:
        response = requests.post(
            RAZORPAY_ORDERS_URL,
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET),
            json={
                "amount": to_paise(order.total),  # Razorpay wants paise
                "currency": "INR",
                "receipt": order.reference,
                "notes": {"order_public_id": str(order.public_id)},
            },
            timeout=15,
        )
        response.raise_for_status()
        gateway_order_id = response.json()["id"]
    except (requests.RequestException, ValueError, KeyError) as exc:
        raise PaymentError(str(exc)) from exc

    order.payment_reference = gateway_order_id
    order.save(update_fields=["payment_reference"])


def checkout_options(order):
    """Options handed to Razorpay's checkout.js on the payment page."""
    return {
        "key": settings.RAZORPAY_KEY_ID,
        "amount": to_paise(order.total),
        "currency": "INR",
        "name": settings.SHOP_NAME,
        "description": f"Order {order.reference}",
        "order_id": order.payment_reference,
        "prefill": {"name": order.full_name, "email": order.email, "contact": order.phone},
        "theme": {"color": "#a85038"},
        "callback_url": settings.SITE_URL + reverse("shop:razorpay_callback", args=[order.public_id]),
        "redirect": True,
    }


def _hmac_hex(secret, message):
    return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()


def verify_razorpay_payment(gateway_order_id, payment_id, signature):
    """Check the signature Razorpay sends to the callback after a successful payment."""
    if not (gateway_order_id and payment_id and signature and settings.RAZORPAY_KEY_SECRET):
        return False
    expected = _hmac_hex(settings.RAZORPAY_KEY_SECRET, f"{gateway_order_id}|{payment_id}".encode())
    return hmac.compare_digest(expected, signature)


def verify_razorpay_webhook(body, signature):
    """Check the X-Razorpay-Signature header on a webhook request."""
    if not (signature and settings.RAZORPAY_WEBHOOK_SECRET):
        return False
    return hmac.compare_digest(_hmac_hex(settings.RAZORPAY_WEBHOOK_SECRET, body), signature)
