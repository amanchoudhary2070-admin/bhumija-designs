from django.db import models
from django.urls import reverse
from django.utils import timezone


class Banner(models.Model):
    """Editable blocks on the home page: the hero slider and the two promo panels."""

    class Placement(models.TextChoices):
        HERO = "hero", "Home page slider"
        PROMO_LEFT = "promo_left", "Promo panel (left, green)"
        PROMO_RIGHT = "promo_right", "Promo panel (right, terracotta)"

    placement = models.CharField(max_length=12, choices=Placement.choices, default=Placement.HERO)
    eyebrow = models.CharField(max_length=80, blank=True, help_text="Small line above the title (slider only).")
    title = models.CharField(max_length=120, help_text="Use a new line to break the title in two.")
    highlight = models.CharField(max_length=80, blank=True, help_text="Coloured words after the title (slider only).")
    text = models.TextField(blank=True)
    button_label = models.CharField(max_length=40, blank=True)
    link = models.CharField(max_length=200, blank=True, help_text="e.g. /shop/ or /category/home-decor/")
    image = models.ImageField(upload_to="banners/", blank=True)
    position = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["placement", "position", "id"]

    def __str__(self):
        return f"{self.get_placement_display()}: {self.title.splitlines()[0] if self.title else ''}"


class Page(models.Model):
    """Simple editable pages: About, policies, FAQs. Body is HTML written by staff."""

    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=140)
    body = models.TextField(help_text="HTML. Use <h2>, <p>, <ul> etc.")
    is_published = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("content:page", args=[self.slug])


class Post(models.Model):
    title = models.CharField(max_length=160)
    slug = models.SlugField(unique=True)
    excerpt = models.CharField(max_length=240, blank=True)
    body = models.TextField(help_text="HTML. Use <h2>, <p>, <ul> etc.")
    cover = models.ImageField(upload_to="blog/", blank=True)
    is_published = models.BooleanField(default=True)
    published_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-published_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("content:post", args=[self.slug])


class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=140, blank=True)
    message = models.TextField()
    is_handled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name}: {self.subject or self.message[:40]}"


class CustomArtRequest(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "New"
        QUOTED = "quoted", "Quote sent"
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"
        CLOSED = "closed", "Closed"

    class Budget(models.TextChoices):
        UNDER_5K = "under-5000", "Under ₹5,000"
        FIVE_TO_15K = "5000-15000", "₹5,000 - ₹15,000"
        FIFTEEN_TO_50K = "15000-50000", "₹15,000 - ₹50,000"
        OVER_50K = "over-50000", "Over ₹50,000"
        NOT_SURE = "not-sure", "Not sure yet"

    status = models.CharField(max_length=12, choices=Status.choices, default=Status.NEW, db_index=True)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    description = models.TextField("What would you like us to create?")
    size = models.CharField("Preferred size", max_length=60, blank=True)
    budget = models.CharField(max_length=20, choices=Budget.choices, default=Budget.NOT_SURE)
    reference_image = models.ImageField("Reference image", upload_to="custom_requests/", blank=True)
    admin_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Custom art request from {self.name}"
