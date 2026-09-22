from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from shop.models import Category, Product

from .forms import ContactForm, CustomArtRequestForm, NewsletterForm
from .models import Banner, Page, Post


def home(request):
    hero_slides = Banner.objects.filter(placement=Banner.Placement.HERO, is_active=True)
    promo_left = Banner.objects.filter(placement=Banner.Placement.PROMO_LEFT, is_active=True).first()
    promo_right = Banner.objects.filter(placement=Banner.Placement.PROMO_RIGHT, is_active=True).first()
    categories = Category.objects.filter(parent=None, show_on_home=True)
    featured = Product.objects.filter(is_active=True, is_featured=True, stock__gt=0)[:6]
    if featured.count() < 6:
        featured = Product.objects.filter(is_active=True, stock__gt=0)[:6]
    return render(request, "content/home.html", {
        "hero_slides": hero_slides,
        "promo_left": promo_left,
        "promo_right": promo_right,
        "categories": categories,
        "featured": featured,
        "newsletter_form": NewsletterForm(),
    })


@require_POST
def newsletter_signup(request):
    form = NewsletterForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, "You're subscribed! Watch your inbox for new arrivals and offers.")
    else:
        messages.error(request, "Please enter a valid email address.")
    return redirect(request.META.get("HTTP_REFERER") or "content:home")


def custom_art(request):
    if request.method == "POST":
        form = CustomArtRequestForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Thank you! We've received your request and will send a quote within 2 working days.")
            return redirect("content:custom_art")
    else:
        form = CustomArtRequestForm()
    return render(request, "content/custom_art.html", {"form": form})


def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Thanks for writing in. We'll get back to you within a day.")
            return redirect("content:contact")
    else:
        form = ContactForm()
    return render(request, "content/contact.html", {"form": form})


def about(request):
    return render(request, "content/about.html")


def page(request, slug):
    obj = get_object_or_404(Page, slug=slug, is_published=True)
    return render(request, "content/page.html", {"page": obj})


def post_list(request):
    posts = Post.objects.filter(is_published=True)
    return render(request, "content/post_list.html", {"posts": posts})


def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug, is_published=True)
    return render(request, "content/post_detail.html", {"post": post})
