import uuid
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg, Count
from django.urls import reverse
from django.utils.text import slugify


def unique_slug(instance, source, max_length=60):
    """Build a slug from `source` that is unique for the instance's model."""
    base = slugify(source)[:max_length] or "item"
    slug, n = base, 2
    model = type(instance)
    while model.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
        slug = f"{base[: max_length - len(str(n)) - 1]}-{n}"
        n += 1
    return slug


class Category(models.Model):
    """Two levels: top-level categories (shown in the menu bar) and their sub-categories."""

    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="children",
        help_text="Leave empty for a top-level category.",
    )
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=80, unique=True, blank=True)
    nav_label = models.CharField(
        max_length=40, blank=True, help_text="Shorter name for the menu bar, e.g. 'Gifts' for 'Gifts & Corporate'."
    )
    ICON_CHOICES = [
        ("painting", "Painting"), ("lotus", "Lotus / motif"), ("home", "Home decor"),
        ("lamp", "Lamp"), ("pot", "Handicraft pot"), ("scarf", "Textile / scarf"),
        ("gift", "Gift box"), ("brush", "Custom art brush"), ("leaf", "Leaf (default)"),
    ]
    icon_key = models.CharField(max_length=20, choices=ICON_CHOICES, default="leaf", help_text="Icon shown in the category circle on the home page.")
    image = models.ImageField(upload_to="categories/", blank=True, help_text="Shown in the round category tiles on the home page.")
    description = models.TextField(blank=True)
    position = models.PositiveSmallIntegerField(default=0, help_text="Lower numbers come first.")
    show_in_nav = models.BooleanField("Show in menu bar", default=True)
    show_on_home = models.BooleanField("Show on home page", default=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["position", "name"]

    def __str__(self):
        return f"{self.parent.name} > {self.name}" if self.parent_id else self.name

    def clean(self):
        if self.parent_id and self.parent.parent_id:
            raise ValidationError({"parent": "Only two levels are supported: choose a top-level category."})
        if self.parent_id and self.parent_id == self.pk:
            raise ValidationError({"parent": "A category can't be its own parent."})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.name, 80)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("shop:category", args=[self.slug])

    @property
    def menu_label(self):
        return self.nav_label or self.name

    def family_ids(self):
        """This category plus its sub-categories (used when listing products)."""
        return [self.pk, *self.children.values_list("pk", flat=True)]


class Artisan(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=110, unique=True, blank=True)
    village = models.CharField("Village / town", max_length=100, blank=True)
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to="artisans/", blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.name, 110)
        super().save(*args, **kwargs)


class Product(models.Model):
    categories = models.ManyToManyField(Category, blank=True, related_name="products")
    artisan = models.ForeignKey(Artisan, null=True, blank=True, on_delete=models.SET_NULL, related_name="products")
    name = models.CharField(max_length=140)
    slug = models.SlugField(max_length=160, unique=True, blank=True)
    description = models.TextField(blank=True)
    details = models.CharField(max_length=200, blank=True, help_text="Short line under the name, e.g. size and material.")

    price = models.DecimalField(
        "Selling price (₹)", max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("1"))]
    )
    compare_at_price = models.DecimalField(
        "MRP (₹)", max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Optional. If higher than the selling price, it is shown struck through with a '% off' label.",
    )
    stock = models.PositiveIntegerField(default=1, help_text="Set to 1 for one-of-a-kind pieces. 0 shows the item as sold.")
    is_active = models.BooleanField(default=True, help_text="Untick to hide the product from the shop entirely.")
    is_featured = models.BooleanField(default=False, help_text="Show on the home page under 'Featured Products'.")

    image = models.ImageField(upload_to="products/", blank=True, help_text="Cover photo.")
    dimensions = models.CharField(max_length=100, blank=True, help_text="e.g. 24 x 36 in")
    materials = models.CharField(max_length=140, blank=True, help_text="e.g. Handmade paper, natural pigments")
    dispatch_days = models.PositiveSmallIntegerField(default=3, help_text="Working days needed to pack and dispatch.")

    # Kept up to date automatically from reviews (see signals.py).
    rating_avg = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal("0"), editable=False)
    rating_count = models.PositiveIntegerField(default=0, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def clean(self):
        if self.compare_at_price is not None and self.price is not None and self.compare_at_price <= self.price:
            raise ValidationError({"compare_at_price": "MRP must be higher than the selling price (or leave it empty)."})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.name, 160)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("shop:product_detail", args=[self.slug])

    @property
    def in_stock(self):
        return self.stock > 0

    @property
    def discount_percent(self):
        if self.compare_at_price and self.compare_at_price > self.price:
            return int(round((1 - self.price / self.compare_at_price) * 100))
        return 0

    @property
    def primary_category(self):
        return self.categories.order_by("parent_id", "position").first()

    def refresh_rating(self):
        agg = self.reviews.filter(is_approved=True).aggregate(avg=Avg("rating"), n=Count("id"))
        avg = Decimal(str(agg["avg"] or 0)).quantize(Decimal("0.01"))
        Product.objects.filter(pk=self.pk).update(rating_avg=avg, rating_count=agg["n"])
        self.rating_avg, self.rating_count = avg, agg["n"]


class ProductImage(models.Model):
    """Extra gallery photos shown on the product page."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="gallery")
    image = models.ImageField(upload_to="products/")
    alt_text = models.CharField(max_length=140, blank=True)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self):
        return f"Photo for {self.product}"


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=120, blank=True)
    body = models.TextField(blank=True)
    verified_purchase = models.BooleanField(default=False, editable=False)
    is_approved = models.BooleanField(default=True, help_text="Untick to hide a review without deleting it.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["product", "user"], name="one_review_per_user_per_product")]

    def __str__(self):
        return f"{self.rating}★ {self.product} by {self.user}"


class WishlistItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wishlist_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["user", "product"], name="one_wishlist_row_per_product")]

    def __str__(self):
        return f"{self.user} ♥ {self.product}"


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Awaiting payment"
        PAID = "paid", "Confirmed"
        SHIPPED = "shipped", "Shipped"
        CANCELLED = "cancelled", "Cancelled"
        REVIEW = "review", "Needs review"

    # Unguessable id used in customer-facing URLs (never expose sequential ids).
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="orders")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING, db_index=True)

    email = models.EmailField()
    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20, blank=True)
    address_line1 = models.CharField("Address", max_length=200)
    address_line2 = models.CharField("Address line 2", max_length=200, blank=True)
    city = models.CharField("City / town", max_length=100)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField("PIN code", max_length=20)
    country = models.CharField(max_length=100, default="India")

    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    payment_provider = models.CharField(max_length=20, blank=True)
    payment_reference = models.CharField("Gateway order id", max_length=255, blank=True, db_index=True)
    payment_id = models.CharField("Gateway payment id", max_length=255, blank=True)

    courier = models.CharField(max_length=80, blank=True)
    tracking_number = models.CharField(max_length=100, blank=True)
    internal_note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order {self.reference} ({self.get_status_display()})"

    @property
    def reference(self):
        """Short, human-friendly order number shown to customers."""
        return f"BD{self.pk:06d}"

    def get_absolute_url(self):
        return reverse("shop:order_detail", args=[self.public_id])


class OrderItem(models.Model):
    """A snapshot of what was bought, so later edits to a product don't rewrite history."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, null=True, on_delete=models.SET_NULL, related_name="+")
    name = models.CharField(max_length=140)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity} × {self.name}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity
