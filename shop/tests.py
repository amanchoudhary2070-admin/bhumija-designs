from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from .cart import calculate_shipping
from .forms import clean_indian_mobile
from .models import Artisan, Category, Order, Product, Review, WishlistItem
from .services import fulfill_order

User = get_user_model()

CHECKOUT_DATA = {
    "full_name": "Priya Sharma", "email": "priya@example.com", "phone": "98765 43210",
    "address_line1": "12 MG Road", "address_line2": "", "city": "Patna",
    "state": "Bihar", "postal_code": "800001",
}


def make_category(name="Madhubani Paintings"):
    return Category.objects.get_or_create(name=name)[0]


def make_product(name="Radha Krishna Painting", price="4999.00", stock=3, category=None, **kwargs):
    p = Product.objects.create(name=name, price=Decimal(price), stock=stock, **kwargs)
    p.categories.add(category or make_category())
    return p


def make_user(email="buyer@example.com", password="StrongPass123"):
    u = User.objects.create_user(username=email, email=email, password=password)
    return u


@override_settings(PAYMENT_PROVIDER="dev", SHIPPING_FLAT_RATE=Decimal("99"), FREE_SHIPPING_THRESHOLD=Decimal("1499"))
class ShopTests(TestCase):
    def add(self, product, quantity=1):
        return self.client.post(reverse("shop:cart_add", args=[product.pk]), {"quantity": quantity})

    def place_order(self):
        response = self.client.post(reverse("shop:checkout"), CHECKOUT_DATA)
        return response, Order.objects.latest("id")

    # -- Indian-specific validation --------------------------------------------

    def test_indian_mobile_normalisation(self):
        self.assertEqual(clean_indian_mobile("98765 43210"), "+919876543210")
        self.assertEqual(clean_indian_mobile("+91-98765-43210"), "+919876543210")
        self.assertEqual(clean_indian_mobile("09876543210"), "+919876543210")
        with self.assertRaises(Exception):
            clean_indian_mobile("12345")  # too short / doesn't start 6-9

    def test_checkout_rejects_bad_pin_and_phone(self):
        self.add(make_product())
        bad = dict(CHECKOUT_DATA, postal_code="1234", phone="12345")
        self.client.post(reverse("shop:checkout"), bad)
        self.assertEqual(Order.objects.count(), 0)

    # -- catalogue ---------------------------------------------------------------

    def test_home_and_listing_render(self):
        make_product()
        self.assertContains(self.client.get(reverse("content:home")), "Bhoomija")
        self.assertContains(self.client.get(reverse("shop:product_list")), "Radha Krishna")

    def test_category_family_includes_subcategory_products(self):
        top = make_category("Madhubani Paintings")
        child = Category.objects.create(name="Canvas Paintings", parent=top)
        p = Product.objects.create(name="Tree of Life", price=Decimal("1000"), stock=1)
        p.categories.add(child)
        response = self.client.get(top.get_absolute_url())
        self.assertContains(response, "Tree of Life")

    def test_sold_out_products_listed_last(self):
        make_product(name="Sold Piece", stock=0)
        make_product(name="Available Piece", stock=2)
        response = self.client.get(reverse("shop:product_list"))
        names = [p.name for p in response.context["page"]]
        self.assertEqual(names, ["Available Piece", "Sold Piece"])

    def test_price_and_rating_filters(self):
        make_product(name="Cheap", price="400")
        make_product(name="Costly", price="5000")
        response = self.client.get(reverse("shop:product_list"), {"min_price": "1000"})
        names = [p.name for p in response.context["page"]]
        self.assertEqual(names, ["Costly"])

    def test_search_matches_name(self):
        make_product(name="Terracotta Vase")
        make_product(name="Silk Stole")
        response = self.client.get(reverse("shop:product_list"), {"q": "terracotta"})
        self.assertContains(response, "Terracotta Vase")
        self.assertNotContains(response, "Silk Stole")

    def test_discount_percent(self):
        p = make_product(price="4999", stock=1)
        p.compare_at_price = Decimal("6499")
        p.save()
        self.assertEqual(p.discount_percent, 23)

    # -- cart ---------------------------------------------------------------------

    def test_cart_totals_and_free_shipping_threshold(self):
        p = make_product(price="800", stock=5)
        self.add(p, 2)
        cart = self.client.get(reverse("shop:cart")).context["cart"]
        self.assertEqual(cart.subtotal, Decimal("1600.00"))
        self.assertEqual(cart.shipping, Decimal("0.00"))  # over ₹1499 threshold
        self.assertEqual(cart.total, Decimal("1600.00"))

    def test_shipping_flat_rate_below_threshold(self):
        self.assertEqual(calculate_shipping(Decimal("500")), Decimal("99.00"))
        self.assertEqual(calculate_shipping(Decimal("1499")), Decimal("0.00"))

    def test_quantity_capped_at_stock(self):
        p = make_product(stock=2)
        self.add(p, 10)
        self.assertEqual(len(self.client.get(reverse("shop:cart")).context["cart"]), 2)

    def test_order_uses_server_side_prices(self):
        p = make_product(price="4999", stock=5)
        self.add(p, 2)
        tampered = dict(CHECKOUT_DATA, total="1", subtotal="1")
        self.client.post(reverse("shop:checkout"), tampered)
        order = Order.objects.get()
        self.assertEqual(order.subtotal, Decimal("9998.00"))
        self.assertEqual(order.status, Order.Status.PENDING)

    # -- checkout / dev payment ----------------------------------------------------

    def test_full_purchase_flow_dev_provider(self):
        p = make_product(stock=3)
        self.add(p, 1)
        _, order = self.place_order()
        self.assertEqual(order.phone, "+919876543210")
        response = self.client.post(reverse("shop:dev_pay", args=[order.public_id]), {"action": "pay"})
        self.assertRedirects(response, order.get_absolute_url())
        order.refresh_from_db(); p.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PAID)
        self.assertEqual(p.stock, 2)
        self.assertEqual(len(mail.outbox), 2)

    def test_fulfilment_is_idempotent(self):
        p = make_product(stock=3)
        self.add(p)
        _, order = self.place_order()
        self.assertTrue(fulfill_order(order.pk))
        self.assertFalse(fulfill_order(order.pk))
        p.refresh_from_db()
        self.assertEqual(p.stock, 2)

    def test_last_piece_race_flags_second_order(self):
        p = make_product(name="One-off", stock=1)
        self.add(p)
        _, order_a = self.place_order()
        self.client.cookies.clear()
        self.add(p)
        _, order_b = self.place_order()
        fulfill_order(order_a.pk)
        fulfill_order(order_b.pk)
        p.refresh_from_db(); order_a.refresh_from_db(); order_b.refresh_from_db()
        self.assertEqual(p.stock, 0)
        self.assertEqual(order_a.status, Order.Status.PAID)
        self.assertEqual(order_b.status, Order.Status.REVIEW)

    def test_dev_pay_blocked_outside_dev_provider(self):
        with override_settings(PAYMENT_PROVIDER="razorpay", RAZORPAY_KEY_ID="x", RAZORPAY_KEY_SECRET="y"):
            p = make_product(stock=1)
            self.add(p)
            self.assertEqual(self.client.get(reverse("shop:dev_pay", args=["00000000-0000-0000-0000-000000000000"])).status_code, 404)

    # -- reviews & wishlist (auth-gated) -------------------------------------------

    def test_wishlist_requires_login(self):
        p = make_product()
        response = self.client.post(reverse("shop:wishlist_toggle", args=[p.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response["Location"])
        self.assertEqual(WishlistItem.objects.count(), 0)

    def test_wishlist_toggle_add_and_remove(self):
        p = make_product()
        make_user()
        self.client.login(username="buyer@example.com", password="StrongPass123")
        self.client.post(reverse("shop:wishlist_toggle", args=[p.pk]))
        self.assertEqual(WishlistItem.objects.filter(product=p).count(), 1)
        self.client.post(reverse("shop:wishlist_toggle", args=[p.pk]))
        self.assertEqual(WishlistItem.objects.filter(product=p).count(), 0)

    def test_review_updates_product_rating(self):
        p = make_product()
        make_user()
        self.client.login(username="buyer@example.com", password="StrongPass123")
        self.client.post(reverse("shop:review_create", args=[p.slug]), {"rating": 4, "title": "Lovely", "body": "Great craftsmanship."})
        p.refresh_from_db()
        self.assertEqual(p.rating_count, 1)
        self.assertEqual(p.rating_avg, Decimal("4.00"))

    def test_review_requires_login(self):
        p = make_product()
        response = self.client.post(reverse("shop:review_create", args=[p.slug]), {"rating": 5})
        self.assertEqual(Review.objects.count(), 0)
        self.assertEqual(response.status_code, 302)


@override_settings(PAYMENT_PROVIDER="razorpay", RAZORPAY_KEY_ID="rzp_test_x", RAZORPAY_KEY_SECRET="secret_x", RAZORPAY_WEBHOOK_SECRET="whsec_x")
class RazorpayTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(name="Vase", price=Decimal("2000"), stock=3)
        self.client.post(reverse("shop:cart_add", args=[self.product.pk]), {"quantity": 2})

    def start_checkout(self):
        with mock.patch("shop.payments.requests.post") as post:
            post.return_value = mock.Mock(status_code=200, json=lambda: {"id": "order_RZP123"})
            post.return_value.raise_for_status = lambda: None
            response = self.client.post(reverse("shop:checkout"), CHECKOUT_DATA)
        return response, post, Order.objects.get()

    def test_checkout_creates_razorpay_order_with_paise_amount(self):
        response, post, order = self.start_checkout()
        self.assertEqual(response.status_code, 302)
        kwargs = post.call_args.kwargs
        self.assertEqual(kwargs["json"]["amount"], 400000)  # 2000*2 subtotal, free shipping over ₹1499
        self.assertEqual(kwargs["json"]["currency"], "INR")
        order.refresh_from_db()
        self.assertEqual(order.payment_reference, "order_RZP123")
        self.assertEqual(order.status, Order.Status.PENDING)

    def test_razorpay_start_failure_cancels_order(self):
        import requests
        with mock.patch("shop.payments.requests.post", side_effect=requests.exceptions.ConnectionError("network down")):
            response = self.client.post(reverse("shop:checkout"), CHECKOUT_DATA)
        self.assertRedirects(response, reverse("shop:cart"))
        self.assertEqual(Order.objects.get().status, Order.Status.CANCELLED)

    def test_callback_with_valid_signature_marks_paid(self):
        from shop import payments
        _, _, order = self.start_checkout()
        sig = payments._hmac_hex("secret_x", f"{order.payment_reference}|pay_abc".encode())
        response = self.client.post(reverse("shop:razorpay_callback", args=[order.public_id]), {
            "razorpay_order_id": order.payment_reference, "razorpay_payment_id": "pay_abc", "razorpay_signature": sig,
        })
        self.assertRedirects(response, order.get_absolute_url())
        order.refresh_from_db(); self.product.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PAID)
        self.assertEqual(order.payment_id, "pay_abc")
        self.assertEqual(self.product.stock, 1)

    def test_callback_with_bad_signature_does_not_mark_paid(self):
        _, _, order = self.start_checkout()
        self.client.post(reverse("shop:razorpay_callback", args=[order.public_id]), {
            "razorpay_order_id": order.payment_reference, "razorpay_payment_id": "pay_abc", "razorpay_signature": "forged",
        })
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PENDING)

    def test_webhook_requires_valid_signature(self):
        response = self.client.post(reverse("shop:razorpay_webhook"), data="{}", content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_webhook_marks_paid_and_is_idempotent(self):
        import json
        from shop import payments
        _, _, order = self.start_checkout()
        body = json.dumps({
            "event": "payment.captured",
            "payload": {"payment": {"entity": {"id": "pay_xyz", "order_id": order.payment_reference}}},
        }).encode()
        sig = payments._hmac_hex("whsec_x", body)
        for _ in range(2):  # webhooks can be retried by the gateway
            response = self.client.post(reverse("shop:razorpay_webhook"), data=body, content_type="application/json", HTTP_X_RAZORPAY_SIGNATURE=sig)
            self.assertEqual(response.status_code, 200)
        order.refresh_from_db(); self.product.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PAID)
        self.assertEqual(self.product.stock, 1)  # decremented once, not twice


class AccountsTests(TestCase):
    def test_signup_creates_account_and_logs_in(self):
        response = self.client.post(reverse("accounts:signup"), {
            "email": "new@example.com", "full_name": "New User", "phone": "",
            "password1": "StrongPass123", "password2": "StrongPass123",
        })
        self.assertRedirects(response, reverse("accounts:dashboard"))
        self.assertTrue(User.objects.filter(email="new@example.com").exists())

    def test_signup_rejects_mismatched_passwords(self):
        self.client.post(reverse("accounts:signup"), {
            "email": "new@example.com", "full_name": "New User",
            "password1": "StrongPass123", "password2": "Different123",
        })
        self.assertFalse(User.objects.filter(email="new@example.com").exists())

    def test_login_with_email(self):
        make_user("login@example.com", "StrongPass123")
        response = self.client.post(reverse("accounts:login"), {"username": "login@example.com", "password": "StrongPass123"})
        self.assertRedirects(response, reverse("accounts:dashboard"))

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertEqual(response.status_code, 302)


class ContentTests(TestCase):
    def test_newsletter_signup(self):
        from content.models import Subscriber
        self.client.post(reverse("content:newsletter_signup"), {"email": "fan@example.com"}, HTTP_REFERER="/")
        self.assertTrue(Subscriber.objects.filter(email="fan@example.com").exists())

    def test_contact_form_saves_message(self):
        from content.models import ContactMessage
        self.client.post(reverse("content:contact"), {"name": "Rahul", "email": "rahul@example.com", "subject": "Hi", "message": "Question about an order."})
        self.assertTrue(ContactMessage.objects.filter(email="rahul@example.com").exists())

    def test_custom_art_request_saves(self):
        from content.models import CustomArtRequest
        self.client.post(reverse("content:custom_art"), {
            "name": "Meera", "email": "meera@example.com", "phone": "", "description": "A family portrait please.",
            "size": "16x20", "budget": "5000-15000",
        })
        self.assertTrue(CustomArtRequest.objects.filter(email="meera@example.com").exists())

    def test_track_order_by_number_and_email(self):
        make_product = Product.objects.create(name="X", price=Decimal("100"), stock=1)
        order = Order.objects.create(email="e@example.com", full_name="A", address_line1="1 Rd", city="Patna", postal_code="800001", subtotal=100, shipping=0, total=100)
        response = self.client.post(reverse("shop:track_order"), {"order_number": order.reference, "email": "e@example.com"})
        self.assertRedirects(response, order.get_absolute_url())
