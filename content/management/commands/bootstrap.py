"""
Runs automatically on every deploy (see Procfile's "release" step). Safe to run
many times: creates the admin login only if it doesn't exist yet, and only seeds
demo data if the shop is still empty. This lets a host with no shell/SSH access
on its free tier (like Render's free web services) still end up with a working
admin account and a browsable catalogue, with nothing to type after deploying.
"""
import os

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand

from shop.models import Product

User = get_user_model()


class Command(BaseCommand):
    help = "Create the admin login from env vars (if missing) and seed demo data (if the shop is empty)."

    def handle(self, *args, **options):
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        if email and password and not User.objects.filter(username=email).exists():
            User.objects.create_superuser(username=email, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f"Created admin login: {email}"))
        elif not email or not password:
            self.stdout.write("Skipped admin creation: set DJANGO_SUPERUSER_EMAIL and DJANGO_SUPERUSER_PASSWORD to enable it.")
        else:
            self.stdout.write("Admin login already exists, skipped.")

        if os.environ.get("SEED_DEMO_DATA", "1") == "1" and not Product.objects.exists():
            call_command("seed_demo")
        else:
            self.stdout.write("Skipped demo data (already seeded, or SEED_DEMO_DATA=0).")
