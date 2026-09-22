from decimal import Decimal, InvalidOperation

from django import template
from django.conf import settings

register = template.Library()


def _group_indian(digits):
    """1234567 -> 12,34,567"""
    if len(digits) <= 3:
        return digits
    head, tail = digits[:-3], digits[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return ",".join(parts + [tail])


@register.filter
def inr(value):
    """Format a number as rupees with Indian digit grouping: 4999 -> ₹4,999, 129999.5 -> ₹1,29,999.50"""
    try:
        amount = Decimal(value).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError):
        return ""
    sign = "-" if amount < 0 else ""
    whole, _, paise = f"{abs(amount):.2f}".partition(".")
    text = _group_indian(whole)
    if paise != "00":
        text += "." + paise
    return f"{sign}{settings.CURRENCY_SYMBOL}{text}"


@register.filter
def star_percent(rating):
    """Width (0-100) of the filled part of a 5-star rating bar."""
    try:
        return int(round(float(rating) / 5 * 100))
    except (TypeError, ValueError):
        return 0
