"""
Session-backed shopping cart.

The session only stores {product_id: quantity}. Prices, names and stock are always
read from the database, so a customer can never influence what they are charged.
"""
from dataclasses import dataclass
from decimal import Decimal

from django.conf import settings

from .models import Product

CENTS = Decimal("0.01")


def money(value):
    return Decimal(value).quantize(CENTS)


def calculate_shipping(subtotal):
    """Flat rate, free above the threshold (if one is set). No shipping on an empty cart."""
    if subtotal <= 0:
        return money(0)
    threshold = settings.FREE_SHIPPING_THRESHOLD
    if threshold > 0 and subtotal >= threshold:
        return money(0)
    return money(settings.SHIPPING_FLAT_RATE)


@dataclass
class CartLine:
    product: Product
    quantity: int

    @property
    def line_total(self):
        return money(self.product.price * self.quantity)


class Cart:
    SESSION_KEY = "cart"

    def __init__(self, request):
        self.session = request.session
        self._data = dict(self.session.get(self.SESSION_KEY, {}))
        self._lines = None
        self.warnings = []

    # -- mutation --------------------------------------------------------------

    def add(self, product, quantity=1, replace=False):
        key = str(product.pk)
        new_qty = quantity if replace else self._data.get(key, 0) + quantity
        new_qty = min(new_qty, product.stock, settings.MAX_QUANTITY_PER_LINE)
        if new_qty < 1:
            self._data.pop(key, None)
        else:
            self._data[key] = new_qty
        self._save()

    def remove(self, product_id):
        self._data.pop(str(product_id), None)
        self._save()

    def clear(self):
        self._data = {}
        self._save()

    def _save(self):
        self.session[self.SESSION_KEY] = self._data
        self.session.modified = True
        self._lines = None

    # -- reading ---------------------------------------------------------------

    def __len__(self):
        """Number of items, computed from the session only (no database query)."""
        return sum(self._data.values())

    def lines(self):
        """Cart lines, reconciled against the database (availability and stock)."""
        if self._lines is None:
            self._load()
        return self._lines

    def _load(self):
        ids = [int(pk) for pk in self._data]
        products = Product.objects.filter(pk__in=ids, is_active=True).in_bulk()
        lines, warnings, changed = [], [], False

        for key, qty in list(self._data.items()):
            product = products.get(int(key))
            if product is None or product.stock < 1:
                name = f"“{product.name}”" if product else "An item"
                warnings.append(f"{name} is no longer available and was removed from your cart.")
                del self._data[key]
                changed = True
                continue
            if qty > product.stock:
                warnings.append(
                    f"Only {product.stock} of “{product.name}” left, so we adjusted your quantity."
                )
                qty = self._data[key] = product.stock
                changed = True
            lines.append(CartLine(product=product, quantity=qty))

        if changed:
            self._save()
        self._lines = lines
        self.warnings = warnings

    @property
    def subtotal(self):
        return money(sum((line.line_total for line in self.lines()), Decimal("0")))

    @property
    def shipping(self):
        return calculate_shipping(self.subtotal)

    @property
    def total(self):
        return self.subtotal + self.shipping

    @property
    def free_shipping_progress(self):
        """0-100: how close the subtotal is to the free-shipping threshold."""
        threshold = settings.FREE_SHIPPING_THRESHOLD
        if threshold <= 0:
            return 100
        return int(min(100, self.subtotal / threshold * 100))

    @property
    def free_shipping_remaining(self):
        """How much more to spend for free shipping, or None if not applicable."""
        threshold = settings.FREE_SHIPPING_THRESHOLD
        if threshold <= 0 or self.subtotal <= 0 or self.subtotal >= threshold:
            return None
        return money(threshold - self.subtotal)
