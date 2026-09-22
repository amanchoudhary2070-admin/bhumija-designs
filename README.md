# Bhoomija Designs: a Django e-commerce marketplace starter

A full storefront for handcrafted goods (Madhubani art, home decor, handicrafts):
catalogue with categories and filters, accounts, wishlist, reviews, cart, checkout,
Razorpay payments (UPI/cards/netbanking/wallets), order emails, a custom-art request
form, a blog, and a Django admin to run all of it.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo        # demo categories, artisans, 25 products, banners
python manage.py runserver
```

- Shop: http://localhost:8000
- Admin: http://localhost:8000/admin/

`seed_demo` also generates simple placeholder photos for every product and artisan
(soft colour + a dot-medallion motif — original artwork drawn in code, not a stock
image) so the site looks complete immediately. Replace them with real product
photography in the admin whenever you're ready; `seed_demo --no-images` skips that
step if you'd rather start with blank images. Run the tests any time: `python manage.py test` (34 tests).

## What's different from a generic starter

This one is built for an Indian handicrafts marketplace specifically:

- **Currency & formatting**: ₹ throughout, Indian digit grouping (₹1,29,999), no paise shown when whole.
- **Payments: Razorpay**, not Stripe — supports UPI, cards, netbanking and wallets (Paytm included) in one checkout. Called directly over its REST API (`shop/payments.py`), no SDK dependency.
- **Indian address form**: state dropdown, 10-digit mobile number validation (normalises `98765 43210`, `+91...`, `0...` to `+91XXXXXXXXXX`), 6-digit PIN code validation.
- **Categories with sub-categories**, a filter sidebar (price, rating, in-stock), sort, and search — the "Shop by Category" home page grid and dropdown mega-menu from the mockup.
- **Accounts**: email-based login/signup, order history, a wishlist, and product reviews (with a "Verified purchase" tag when the reviewer actually bought the item).
- **Custom Art request form** with a reference-image upload, separate from checkout, matching the "Custom Art Just for You" flow in the mockup.
- **Editable homepage**: hero slider, two promo panels and featured products are all `Banner`/`Product.is_featured` rows in the admin, not hardcoded.

## Project layout

```
config/             settings (all from env vars), root urls
shop/
  models.py          Category (2-level), Artisan, Product, Review, WishlistItem, Order, OrderItem
  cart.py            session cart + shipping rules
  services.py        create_order_from_cart(), fulfill_order()   <- money & stock logic
  payments.py        Razorpay order creation + signature verification (or the dev simulator)
  views/             catalog.py (listing/filters/reviews/wishlist), cart.py, checkout.py
  templatetags/      icons.py (inline SVG icon set), shop_extras.py (₹ formatting, star %)
  management/commands/_placeholder_art.py   generates the original placeholder photos
  templates/shop/, static/shop/ (style.css, shop.js, self-hosted fonts)
content/             home page, about, contact, custom art, blog, policy pages, banners
accounts/            signup/login/dashboard/orders/profile/password reset
```

## How the important parts work

**Prices are never taken from the browser.** The cart stores only `{product_id: quantity}`.
At checkout the server reads prices from the database and writes an `Order` with an
`OrderItem` snapshot of name and price.

**A payment is confirmed by Razorpay, not the browser redirect.** After paying, the
customer is sent to `/order/<id>/razorpay/callback/`, which Razorpay POSTs to with a
signature proving the payment happened — that signature is verified on the server
before `fulfill_order()` runs. A `razorpay.webhook` endpoint is also wired up as a
backup path for customers who close the tab before the callback fires. Anyone can visit
an order's URL; only a validly signed request from Razorpay marks it paid.

**`fulfill_order()` is idempotent.** Both the callback and the webhook can fire for the
same payment. Only the first call on a pending order marks it paid, takes stock, and
sends emails.

**Last-piece races are handled.** Stock is decremented with a conditional UPDATE
(`WHERE stock >= quantity`). If two people pay for the same one-of-a-kind piece, the
first payment wins and the second order is flagged **Needs review**, with a note and an
email to you, so you can refund or contact them.

**Reviews and ratings** use a Django signal (`shop/signals.py`) to keep
`Product.rating_avg`/`rating_count` in sync whenever a review is saved or deleted —
no need to recompute anywhere else.

## Configuration

Everything is env vars (see `.env.example`): shop name/tagline/contact, shipping rate
and free-shipping threshold, currency-adjacent bits, social links, payment provider.
To restyle, edit the tokens at the top of `shop/static/shop/style.css` (colours sampled
from the mockup) and the two font families in the `@font-face` rules (fonts are
self-hosted under `shop/static/shop/fonts/`, so nothing is fetched from Google Fonts
at runtime).

## Taking real payments with Razorpay

1. Create a Razorpay account (razorpay.com) and, from Settings → API Keys, generate a
   **test mode** Key ID and Key Secret.
2. Set in `.env`:
   ```
   PAYMENT_PROVIDER=razorpay
   RAZORPAY_KEY_ID=rzp_test_...
   RAZORPAY_KEY_SECRET=...
   SITE_URL=http://localhost:8000
   ```
3. In the Razorpay dashboard, add a webhook pointing to `https://YOUR-DOMAIN/webhooks/razorpay/`
   for the `payment.captured` and `order.paid` events, and put its signing secret in
   `RAZORPAY_WEBHOOK_SECRET`. (For local testing you can skip this — the callback alone
   is enough to confirm a payment; the webhook is a backup path.)
4. Check out with a [Razorpay test card or test UPI ID](https://razorpay.com/docs/payments/payments/test-card-upi-details/).
5. Switch `RAZORPAY_KEY_ID`/`RAZORPAY_KEY_SECRET` to your live keys (and add a live-mode
   webhook) when you're ready to accept real payments — Razorpay requires KYC/business
   verification before live mode activates.

## Deploying

Any host that runs Python works (Render, Railway, Fly.io, a VPS). A `Procfile` is included,
and `python manage.py bootstrap` (wired into the Procfile's `release` step) creates the
admin login from `DJANGO_SUPERUSER_EMAIL`/`DJANGO_SUPERUSER_PASSWORD` and seeds demo data
automatically on first deploy — useful on hosts (like Render's free tier) that don't give
you a shell to run `createsuperuser` by hand. It's safe to redeploy; it only acts once.

### Fastest free path: Render.com

1. Put the project in a GitHub repo. If you don't want to use git, GitHub's web UI lets
   you drag the whole project folder onto https://github.com/new to upload it directly.
2. On [render.com](https://render.com), **New → Web Service**, connect the repo. Render
   detects Python automatically (build: `pip install -r requirements.txt`, via the Procfile
   for the rest).
3. **New → PostgreSQL** (free), then copy its **Internal Database URL**.
4. On the web service, add these environment variables:
   ```
   DJANGO_DEBUG=0
   DJANGO_SECRET_KEY=<generate one: python -c "import secrets; print(secrets.token_urlsafe(60))">
   DJANGO_ALLOWED_HOSTS=<your-app>.onrender.com
   CSRF_TRUSTED_ORIGINS=https://<your-app>.onrender.com
   SITE_URL=https://<your-app>.onrender.com
   DATABASE_URL=<the Internal Database URL from step 3>
   PAYMENT_PROVIDER=razorpay
   RAZORPAY_KEY_ID=<your test key, or leave real payment setup for later>
   RAZORPAY_KEY_SECRET=<...>
   DJANGO_SUPERUSER_EMAIL=you@example.com
   DJANGO_SUPERUSER_PASSWORD=<a strong password>
   ```
   (`PAYMENT_PROVIDER` must be `razorpay` here — `dev` is refused whenever `DJANGO_DEBUG=0`,
   so checkout won't work until real or test Razorpay keys are set.)
5. Deploy. Once it's live, your admin login works immediately at `/admin/` — no shell needed.

Free-tier facts worth knowing: the web service sleeps after 15 minutes of no traffic
(next visit takes ~30-60 seconds to wake up), and the free Postgres database expires
after 30 days (create a new one, or move to Render's ~$6-7/month plan to keep it
permanently). Uploaded media (product photos added after deploy) sit on disk that isn't
guaranteed to survive a redeploy — fine for trying things out, but plan on S3/R2/Cloudinary
before this is a real store.

### Checklist for a real store (any host)

- [ ] `DJANGO_DEBUG=0` and a real `DJANGO_SECRET_KEY` — the app refuses to start otherwise
- [ ] `PAYMENT_PROVIDER=razorpay` with live keys — `dev` is refused when debug is off
- [ ] `DJANGO_ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS` / `SITE_URL` set to your real domain
- [ ] **A real database**: `DATABASE_URL` to Postgres, `pip install "psycopg[binary]"`
- [ ] **Persistent media storage**: most hosts wipe local disk on deploy, which would delete
      product photos — use S3, Cloudflare R2 or Cloudinary via `django-storages`
- [ ] Real email via `EMAIL_HOST*` (Resend, Postmark, Brevo, ...)
- [ ] Change `ADMIN_URL` to something non-obvious
- [ ] Run `migrate`, `collectstatic`, `createsuperuser`; replace demo products/photos
- [ ] Place a real test order in Razorpay test mode before switching to live keys

## Not included (natural next steps)

- Coupon codes, weight/zone-based shipping, GST-itemised invoices
- Product variants (size/colour), stock reservation during checkout
- Payout/refund automation (handle refunds in the Razorpay dashboard, then set the
  order to *Cancelled* in the Django admin)
- Real photography — placeholder art is generated for demo products; swap it in the admin
