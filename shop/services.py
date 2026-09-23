"""Order creation and fulfilment. Keep money- and stock-related logic in this file."""
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import F
from django.template.loader import render_to_string
from django.utils import timezone

from .models import Order, OrderItem, Product

logger = logging.getLogger(__name__)


class EmptyCartError(Exception):
    pass


@transaction.atomic
def create_order_from_cart(cart, customer_data, user=None):
    """
    Create a pending order using prices read from the database (never from the browser).
    `customer_data` is the cleaned data from the checkout form.
    """
    lines = cart.lines()
    if not lines:
        raise EmptyCartError

    order = Order.objects.create(
        **customer_data,
        user=user if (user and user.is_authenticated) else None,
        subtotal=cart.subtotal,
        shipping=cart.shipping,
        total=cart.total,
        payment_provider=settings.PAYMENT_PROVIDER,
    )
    OrderItem.objects.bulk_create(
        OrderItem(
            order=order,
            product=line.product,
            seller=line.product.seller,
            name=line.product.name,
            unit_price=line.product.price,
            quantity=line.quantity,
        )
        for line in lines
    )
    return order


def fulfill_order(order_id, payment_reference="", payment_id=""):
    """
    Mark an order as paid and take its items out of stock.

    Safe to call more than once (payment gateways retry webhooks, and the customer's
    browser callback and the gateway webhook both arrive): only the first call on a
    pending order does anything. Returns True if this call did the work.

    Stock is decremented with a conditional UPDATE, so two simultaneous buyers of a
    one-of-a-kind piece can never both succeed. If an item sold out between checkout
    and payment, the order is flagged "Needs review" so you can refund or contact
    the customer.
    """
    with transaction.atomic():
        order = Order.objects.select_for_update().get(pk=order_id)
        if order.status != Order.Status.PENDING:
            return False

        sold_out = []
        for item in order.items.all():
            taken = 0
            if item.product_id:
                taken = Product.objects.filter(pk=item.product_id, stock__gte=item.quantity).update(
                    stock=F("stock") - item.quantity
                )
            if not taken:
                sold_out.append(item.name)

        order.status = Order.Status.REVIEW if sold_out else Order.Status.PAID
        order.paid_at = timezone.now()
        if payment_reference:
            order.payment_reference = payment_reference
        if payment_id:
            order.payment_id = payment_id
        if sold_out:
            order.internal_note = (
                "Paid, but no longer in stock when payment arrived: " + ", ".join(sold_out)
                + ". Refund or contact the customer.\n" + order.internal_note
            )
        order.save()

    try:
        send_order_emails(order)
    except Exception:  # never fail a payment callback because SMTP is down
        logger.exception("Could not send emails for order %s", order.pk)
    return True


def _email_context(order):
    return {
        "order": order,
        "items": order.items.all(),
        "SHOP_NAME": settings.SHOP_NAME,
        "SITE_URL": settings.SITE_URL,
        "CURRENCY_SYMBOL": settings.CURRENCY_SYMBOL,
    }


def send_order_emails(order):
    context = _email_context(order)
    send_mail(
        f"Your {settings.SHOP_NAME} order {order.reference}",
        render_to_string("shop/email/order_confirmation.txt", context),
        settings.DEFAULT_FROM_EMAIL,
        [order.email],
    )
    flag = " (NEEDS REVIEW)" if order.status == Order.Status.REVIEW else ""
    send_mail(
        f"New order {order.reference}{flag}: {settings.CURRENCY_SYMBOL}{order.total}",
        render_to_string("shop/email/owner_new_order.txt", context),
        settings.DEFAULT_FROM_EMAIL,
        [settings.SHOP_OWNER_EMAIL],
    )


def send_shipped_email(order):
    send_mail(
        f"Your {settings.SHOP_NAME} order {order.reference} is on its way",
        render_to_string("shop/email/order_shipped.txt", _email_context(order)),
        settings.DEFAULT_FROM_EMAIL,
        [order.email],
    )
