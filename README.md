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

## Seller marketplace

Anyone can apply to sell on the site at `/sell/apply/` — they get their own dashboard to
add products (with their own photos, price, stock) once an admin approves their account
(**Django admin → Seller profiles → select → "Approve selected sellers"**). Approved
sellers get a public shop page (`/seller/<their-shop>/`), their products show a "Sold by"
link on the product page, and they can see (only) their own items across all orders and
mark them shipped from `/sell/orders/`.

**What this does not do yet**: all payments still go to your own Razorpay account — there's
no automatic payout split to each seller's bank account. That requires Razorpay Route (a
separate "marketplace payments" product where each seller completes their own KYC on
Razorpay's platform) — a meaningful extra integration, not included here. Until then, settle
with sellers manually (bank transfer, on whatever schedule you agree), using the seller's
own order list as the record of what they sold.

## Keeping uploaded photos permanently (Cloudflare R2)

Hosts without a persistent disk (Render's free tier included) lose any file written to
local disk on every restart. The demo product photos self-heal automatically (see
below), but **real photos a seller uploads through `/sell/` will be lost** unless you
point the site at proper object storage. Cloudflare R2 has a genuinely free tier (10 GB,
no egress fees) and needs no code changes — just env vars:

1. Sign up at [cloudflare.com](https://dash.cloudflare.com) → **R2 Object Storage** → create a bucket (any name, e.g. `bhoomija-media`).
2. In the bucket's **Settings**, enable **Public Access** (via the "R2.dev subdomain" option) and copy the public URL it gives you (looks like `pub-xxxxxxxx.r2.dev`) — that's your `AWS_S3_CUSTOM_DOMAIN`.
3. Go to **R2 → Manage API Tokens → Create API Token**, permission "Object Read & Write", scoped to your bucket. Copy the **Access Key ID** and **Secret Access Key** it gives you (shown once).
4. On the same token page, note your **Account ID** (also shown in the R2 dashboard's right sidebar). Your endpoint URL is `https://<account_id>.r2.cloudflarestorage.com`.
5. Set these on Render (Environment tab, same as the other variables):
   ```
   AWS_ACCESS_KEY_ID=<the access key from step 3>
   AWS_SECRET_ACCESS_KEY=<the secret key from step 3>
   AWS_STORAGE_BUCKET_NAME=bhoomija-media
   AWS_S3_ENDPOINT_URL=https://<account_id>.r2.cloudflarestorage.com
   AWS_S3_CUSTOM_DOMAIN=pub-xxxxxxxx.r2.dev
   ```
6. Redeploy. From then on, every uploaded photo (products, seller logos, custom-art references) goes straight to R2 and survives restarts and redeploys. Existing local-disk photos aren't migrated automatically — re-upload them once, or re-run `seed_demo` for the demo catalogue.

Leave all five blank and the site keeps using local disk exactly as before — nothing else changes.

## Self-healing demo photos

Every deploy runs `python manage.py repair_images` (wired into `bootstrap`, itself
wired into the Procfile/Build Command). It checks every product, artisan and banner
photo and regenerates any that's missing from storage — so even without R2 configured,
the *demo* catalogue's placeholder photos reappear automatically after a redeploy on a
host with no persistent disk. This only helps the generated demo images, not real
uploads (those need R2 — see above).

## Deploying

Any host that runs Python works (Render, Railway, Fly.io, a VPS). `python manage.py
bootstrap` creates the admin login from `DJANGO_SUPERUSER_EMAIL`/`DJANGO_SUPERUSER_PASSWORD`,
seeds demo data on first deploy, and repairs any missing photos — useful on hosts (like
Render's free tier) that don't give you a shell to run `createsuperuser` by hand. It's
safe to redeploy; seeding only happens once.

**A Procfile is included, but not every host runs its `release:` line automatically**
(Render's free tier doesn't — that's a paid-only "Pre-Deploy Command" feature there). The
reliable way that works everywhere is to run migrate/collectstatic/bootstrap as part of
the **Build Command** itself, before the app starts — see step 2 below.

### Fastest free path: Render.com

1. Put the project in a GitHub repo. If you don't want to use git, GitHub Desktop
   (desktop.github.com) can publish a whole folder with no command line needed — open it,
   "Add Local Repository" → your project folder → "create a repository" → "Publish repository".
2. On [render.com](https://render.com), **New → Web Service**, connect the repo. Render
   detects Python automatically. In **Settings → Build & Deploy**, set:
   - **Build Command**:
     ```
     pip install -r requirements.txt && python manage.py migrate --noinput && python manage.py collectstatic --noinput && python manage.py bootstrap
     ```
   - **Start Command**: `gunicorn config.wsgi --log-file -`
3. **New → PostgreSQL** (free), then copy its **Internal Database URL**.
4. On the web service, add these environment variables (**Environment** tab → **"Add from .env"** lets you paste this whole block at once):
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
   Double-check `<your-app>.onrender.com` matches your **actual** service URL exactly
   (shown at the top of the service page) — a mismatch here causes a "Bad Request (400)".
   `PAYMENT_PROVIDER` must be `razorpay` — `dev` is refused whenever `DJANGO_DEBUG=0`, but
   `RAZORPAY_KEY_ID`/`SECRET` can be left blank for now: the site still runs fully, only
   the checkout "Pay" button shows a friendly error until real keys are added.
5. Deploy (Manual Deploy → Deploy latest commit, if it doesn't start automatically). Once
   it's live, your admin login works immediately at `/admin/` — no shell needed.

Free-tier facts worth knowing: the web service sleeps after 15 minutes of no traffic
(next visit takes ~30-60 seconds to wake up), and the free Postgres database expires
after 30 days (create a new one, or move to Render's ~$6-7/month plan to keep it
permanently). Uploaded photos need Cloudflare R2 to survive restarts — see above.

### Checklist for a real store (any host)

- [ ] `DJANGO_DEBUG=0` and a real `DJANGO_SECRET_KEY` — the app refuses to start otherwise
- [ ] `PAYMENT_PROVIDER=razorpay` with live keys — `dev` is refused when debug is off
- [ ] `DJANGO_ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS` / `SITE_URL` set to your real domain, matching exactly
- [ ] **A real database**: `DATABASE_URL` to Postgres, `pip install "psycopg[binary]"`
- [ ] **Persistent media storage**: set up Cloudflare R2 (see above) before real sellers upload real photos
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
