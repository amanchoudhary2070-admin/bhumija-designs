"""
Django settings for the handmade shop.

Everything that changes between your laptop and production is read from
environment variables (or a .env file in the project root). See .env.example.
"""
import os
import sys
from decimal import Decimal
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env(name, default=""):
    return os.environ.get(name, default)


def env_bool(name, default=False):
    return env(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    return [item.strip() for item in env(name, default).split(",") if item.strip()]


# --- Core ---------------------------------------------------------------------

DEBUG = env_bool("DJANGO_DEBUG", True)
SECRET_KEY = env("DJANGO_SECRET_KEY", "dev-only-insecure-key-change-me")
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "shop",
    "content",
    "accounts",
    "sellers",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "shop.context_processors.storefront",
            ],
        },
    },
]

# --- Database -----------------------------------------------------------------
# SQLite by default. For Postgres set DATABASE_URL=postgres://user:pass@host/db

DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Internationalisation -----------------------------------------------------

LANGUAGE_CODE = "en-in"
TIME_ZONE = env("TIME_ZONE", "Asia/Kolkata")
USE_I18N = True
USE_TZ = True

# --- Static & media files -----------------------------------------------------
# Static files are served by WhiteNoise. Product photos (media) are stored on
# local disk by default; on most hosts the disk is wiped on every deploy, so use
# object storage (S3, Cloudflare R2, Cloudinary) in production. See README.

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_ROOT.mkdir(exist_ok=True)  # avoids a WhiteNoise warning before the first collectstatic
WHITENOISE_USE_FINDERS = DEBUG
WHITENOISE_AUTOREFRESH = DEBUG
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

_use_manifest = not DEBUG and "test" not in sys.argv
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedManifestStaticFilesStorage"
            if _use_manifest
            else "whitenoise.storage.CompressedStaticFilesStorage"
        )
    },
}

# --- Email --------------------------------------------------------------------
# Emails print to the console until you configure SMTP (Resend, Postmark, Brevo,
# Gmail app password, ...).

if env("EMAIL_HOST"):
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = env("EMAIL_HOST")
    EMAIL_PORT = int(env("EMAIL_PORT", "587"))
    EMAIL_HOST_USER = env("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
    EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", "Shop <orders@example.com>")

# --- Shop settings ------------------------------------------------------------

SITE_URL = env("SITE_URL", "http://localhost:8000").rstrip("/")
SHOP_NAME = env("SHOP_NAME", "Bhoomija Designs")
SHOP_TAGLINE = env("SHOP_TAGLINE", "The Art of Mithila. The Soul of Home.")

# Contact details shown in the footer and used for order / enquiry emails.
SHOP_EMAIL = env("SHOP_EMAIL", "hello@bhoomijadesigns.in")
SHOP_PHONE = env("SHOP_PHONE", "+91 98765 43210")
SHOP_ADDRESS = env("SHOP_ADDRESS", "Darbhanga, Bihar, India")
SHOP_OWNER_EMAIL = env("SHOP_OWNER_EMAIL", SHOP_EMAIL)  # new-order and enquiry alerts go here

SOCIAL_LINKS = {
    "facebook": env("SOCIAL_FACEBOOK", "#"),
    "instagram": env("SOCIAL_INSTAGRAM", "#"),
    "youtube": env("SOCIAL_YOUTUBE", "#"),
    "pinterest": env("SOCIAL_PINTEREST", "#"),
    "linkedin": env("SOCIAL_LINKEDIN", "#"),
}

SHOP_CURRENCY = "INR"      # Razorpay's default currency
CURRENCY_SYMBOL = "\u20b9"  # rupee sign
SHIPPING_FLAT_RATE = Decimal(env("SHIPPING_FLAT_RATE", "99"))
FREE_SHIPPING_THRESHOLD = Decimal(env("FREE_SHIPPING_THRESHOLD", "1499"))  # 0 disables free shipping
MAX_QUANTITY_PER_LINE = 10

# "dev"      = built-in fake checkout, no keys needed (refused when DEBUG is off).
# "razorpay" = real payments: UPI, cards, netbanking and wallets (incl. Paytm).
PAYMENT_PROVIDER = env("PAYMENT_PROVIDER", "dev").lower()
RAZORPAY_KEY_ID = env("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = env("RAZORPAY_KEY_SECRET")
RAZORPAY_WEBHOOK_SECRET = env("RAZORPAY_WEBHOOK_SECRET")

ADMIN_URL = env("ADMIN_URL", "admin/")  # change this in production

# --- Accounts -----------------------------------------------------------------

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "accounts:dashboard"
LOGOUT_REDIRECT_URL = "content:home"
PASSWORD_RESET_TIMEOUT = 60 * 60 * 24  # reset links last 24 hours

# --- Production hardening -----------------------------------------------------

if not DEBUG:
    if SECRET_KEY.startswith("dev-only"):
        raise ImproperlyConfigured("Set DJANGO_SECRET_KEY when DJANGO_DEBUG is off.")
    if PAYMENT_PROVIDER == "dev":
        raise ImproperlyConfigured(
            "PAYMENT_PROVIDER=dev lets anyone mark orders as paid. Use 'razorpay' in production."
        )
    if PAYMENT_PROVIDER not in {"razorpay"}:
        raise ImproperlyConfigured("Set PAYMENT_PROVIDER=razorpay in production.")
    # Note: RAZORPAY_KEY_ID/SECRET are deliberately NOT required here. Without them the
    # site still runs fully (browsing, cart, accounts, admin) — only the "Pay" button on
    # checkout shows a friendly error, via the PaymentError handling in payments.py /
    # views/checkout.py. This lets you deploy and preview the store before Razorpay is
    # set up, then add real keys later with no code or redeploy-logic changes needed.

    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(env("SECURE_HSTS_SECONDS", "3600"))  # raise once HTTPS is confirmed working
    SECURE_CONTENT_TYPE_NOSNIFF = True
