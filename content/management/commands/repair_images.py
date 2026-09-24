"""
Regenerates any placeholder photo that's missing from storage, even though its
Product/Artisan/Banner row already exists in the database. This happens on hosts
without a persistent disk (e.g. Render's free tier): the database (Postgres) survives
a restart, but locally-generated files written during a previous build do not. Safe
and cheap to run on every deploy — it only touches rows whose file is actually gone.
"""
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from content.models import Banner
from shop.management.commands._placeholder_art import artisan_placeholder, banner_placeholder, product_placeholder
from shop.models import Artisan, Product


def _missing(field_file):
    """True if the field has a filename on record but the file itself isn't in storage."""
    return bool(field_file.name) and not field_file.storage.exists(field_file.name)


def _resave(field_file, filename, pil_image):
    import io
    buf = io.BytesIO()
    pil_image.save(buf, format="JPEG", quality=86)
    field_file.save(filename, ContentFile(buf.getvalue()), save=True)


class Command(BaseCommand):
    help = "Regenerate any generated placeholder photo that's missing from storage."

    def handle(self, *args, **options):
        fixed = 0
        for product in Product.objects.exclude(image=""):
            if _missing(product.image):
                _resave(product.image, f"{product.slug}.jpg", product_placeholder(product.name))
                fixed += 1
        for artisan in Artisan.objects.exclude(photo=""):
            if _missing(artisan.photo):
                _resave(artisan.photo, f"{artisan.slug}.jpg", artisan_placeholder(artisan.name))
                fixed += 1
        for banner in Banner.objects.filter(placement=Banner.Placement.HERO).exclude(image=""):
            if _missing(banner.image):
                _resave(banner.image, f"hero-{banner.position}.jpg", banner_placeholder(banner.title))
                fixed += 1

        if fixed:
            self.stdout.write(self.style.SUCCESS(f"Regenerated {fixed} missing placeholder photo(s)."))
        else:
            self.stdout.write("No missing placeholder photos found.")
