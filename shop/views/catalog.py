from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.core.paginator import Paginator
from django.db.models import Case, Count, IntegerField, Q, Value, When
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from ..forms import ReviewForm
from ..models import Artisan, Category, Order, Product, Review, SellerProfile, WishlistItem
from ..templatetags.shop_extras import inr

PAGE_SIZE = 12
RECENTLY_VIEWED_KEY = "recently_viewed"
RECENTLY_VIEWED_MAX = 10

SORTS = {
    "popular": ("Popularity", ("-rating_count", "-rating_avg", "-created_at")),
    "new": ("Newest first", ("-created_at",)),
    "price_asc": ("Price: low to high", ("price", "-created_at")),
    "price_desc": ("Price: high to low", ("-price", "-created_at")),
    "rating": ("Customer rating", ("-rating_avg", "-rating_count")),
}

PRICE_BUCKETS = [("", "500"), ("500", "1000"), ("1000", "2500"), ("2500", "5000"), ("5000", "")]


def _bucket_label(lo, hi):
    if not lo:
        return f"Under {inr(hi)}"
    if not hi:
        return f"Over {inr(lo)}"
    return f"{inr(lo)} - {inr(hi)}"


def _decimal(value):
    try:
        d = Decimal(value)
        return d if d >= 0 else None
    except (InvalidOperation, TypeError):
        return None


def _qs(params, **changes):
    """Query string for the current listing with some parameters changed. Filter changes reset paging."""
    query = {k: v for k, v in params.items() if v not in (None, "")}
    for key, value in changes.items():
        if value in (None, ""):
            query.pop(key, None)
        else:
            query[key] = value
    query.pop("page", None)
    return "?" + urlencode(query) if query else "?"


def product_list(request, category_slug=None, new_arrivals=False):
    category = get_object_or_404(Category, slug=category_slug) if category_slug else None
    products = Product.objects.public()
    if category:
        products = products.filter(categories__in=category.family_ids())

    params = {
        "q": request.GET.get("q", "").strip()[:100],
        "min_price": request.GET.get("min_price", "").strip(),
        "max_price": request.GET.get("max_price", "").strip(),
        "rating": request.GET.get("rating", "").strip(),
        "in_stock": "1" if request.GET.get("in_stock") else "",
        "sort": request.GET.get("sort", "").strip(),
    }
    if params["sort"] not in SORTS:
        params["sort"] = "new" if new_arrivals else "popular"

    for word in params["q"].split()[:6]:
        products = products.filter(
            Q(name__icontains=word) | Q(description__icontains=word)
            | Q(categories__name__icontains=word) | Q(artisan__name__icontains=word)
        )
    min_price, max_price = _decimal(params["min_price"]), _decimal(params["max_price"])
    if min_price is not None:
        products = products.filter(price__gte=min_price)
    if max_price is not None:
        products = products.filter(price__lte=max_price)
    if params["rating"] in {"2", "3", "4"}:
        products = products.filter(rating_avg__gte=int(params["rating"]))
    if params["in_stock"]:
        products = products.filter(stock__gt=0)

    # Available pieces first, sold ones after (they stay visible: they show your past work).
    products = (
        products.annotate(sold=Case(When(stock__gt=0, then=Value(0)), default=Value(1), output_field=IntegerField()))
        .order_by("sold", *SORTS[params["sort"]][1])
        .distinct()
    )
    page = Paginator(products, PAGE_SIZE).get_page(request.GET.get("page"))

    # --- sidebar / toolbar links -------------------------------------------------
    # Sort links keep "sort" out of the default so URLs stay tidy.
    sort_options = [
        {"key": key, "label": label, "selected": key == params["sort"]} for key, (label, _) in SORTS.items()
    ]
    price_links = []
    for lo, hi in PRICE_BUCKETS:
        active = params["min_price"] == lo and params["max_price"] == hi
        price_links.append({
            "label": _bucket_label(lo, hi),
            "url": _qs(params, min_price=None if active else lo, max_price=None if active else hi),
            "active": active,
        })
    rating_links = [
        {"label": f"{n}\u2605 & up", "url": _qs(params, rating=None if params["rating"] == str(n) else str(n)),
         "active": params["rating"] == str(n)}
        for n in (4, 3)
    ]

    chips = []
    if params["q"]:
        chips.append({"label": f"“{params['q']}”", "url": _qs(params, q=None)})
    if min_price is not None or max_price is not None:
        lo = inr(min_price) if min_price is not None else "\u20b90"
        label = f"{lo} - {inr(max_price)}" if max_price is not None else f"Over {lo}"
        chips.append({"label": label, "url": _qs(params, min_price=None, max_price=None)})
    if params["rating"] in {"2", "3", "4"}:
        chips.append({"label": f"{params['rating']}\u2605 & up", "url": _qs(params, rating=None)})
    if params["in_stock"]:
        chips.append({"label": "In stock only", "url": _qs(params, in_stock=None)})

    # Category navigation: sub-categories of the current one, or all top-level categories.
    if category:
        top = category.parent or category
        side_categories = list(top.children.all())
        side_parent = top
    else:
        side_categories = list(Category.objects.filter(parent=None))
        side_parent = None

    if category:
        heading = category.name
    elif params["q"]:
        heading = f"Results for “{params['q']}”"
    elif new_arrivals:
        heading = "New arrivals"
    else:
        heading = "All products"

    return render(request, "shop/product_list.html", {
        "page": page,
        "category": category,
        "side_categories": side_categories,
        "side_parent": side_parent,
        "heading": heading,
        "params": params,
        "hidden_params": {k: v for k, v in params.items() if v and k not in {"sort"}},
        "sort_options": sort_options,
        "price_links": price_links,
        "rating_links": rating_links,
        "in_stock_url": _qs(params, in_stock=None if params["in_stock"] else "1"),
        "chips": chips,
        "clear_url": "?" + urlencode({"sort": params["sort"]}) if chips else "",
        "page_query": _qs(params)[1:] + ("&" if _qs(params) != "?" else ""),
        "new_arrivals": new_arrivals,
    })


def new_arrivals(request):
    return product_list(request, new_arrivals=True)


def category_index(request):
    categories = Category.objects.filter(parent=None).prefetch_related("children")
    return render(request, "shop/category_index.html", {"categories": categories})


def artisan_list(request):
    artisans = Artisan.objects.filter(is_active=True).annotate(piece_count=Count("products", filter=Q(products__is_active=True)))
    return render(request, "shop/artisan_list.html", {"artisans": artisans})


def seller_storefront(request, slug):
    seller = get_object_or_404(SellerProfile, slug=slug, is_approved=True)
    products = Product.objects.public().filter(seller=seller)
    page = Paginator(products, PAGE_SIZE).get_page(request.GET.get("page"))
    return render(request, "shop/seller_storefront.html", {"seller": seller, "page": page})


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.public().select_related("artisan", "seller").prefetch_related("gallery", "categories"), slug=slug
    )
    category = product.primary_category
    related = Product.objects.public().filter(stock__gt=0).exclude(pk=product.pk)
    if category:
        related = related.filter(categories__in=category.family_ids()).distinct()
    related = related[:6]

    reviews = list(product.reviews.filter(is_approved=True).select_related("user")[:20])
    counts = dict(product.reviews.filter(is_approved=True).values_list("rating").annotate(n=Count("id")))
    total = sum(counts.values())
    breakdown = [
        {"stars": s, "count": counts.get(s, 0), "percent": int(counts.get(s, 0) / total * 100) if total else 0}
        for s in (5, 4, 3, 2, 1)
    ]

    user_review = None
    if request.user.is_authenticated:
        user_review = product.reviews.filter(user=request.user).first()

    # Recently viewed: a small session-stored list of product ids, most recent first.
    recent_ids = [pid for pid in request.session.get(RECENTLY_VIEWED_KEY, []) if pid != product.pk]
    recently_viewed = list(Product.objects.public().filter(pk__in=recent_ids[:RECENTLY_VIEWED_MAX]))
    recently_viewed.sort(key=lambda p: recent_ids.index(p.pk))
    recent_ids.insert(0, product.pk)
    request.session[RECENTLY_VIEWED_KEY] = recent_ids[:RECENTLY_VIEWED_MAX]

    return render(request, "shop/product_detail.html", {
        "product": product,
        "category": category,
        "related": related,
        "reviews": reviews,
        "breakdown": breakdown,
        "user_review": user_review,
        "review_form": ReviewForm(instance=user_review),
        "max_quantity": min(product.stock, 10),
        "recently_viewed": recently_viewed,
    })


@require_POST
def review_create(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    if not request.user.is_authenticated:
        return redirect_to_login(product.get_absolute_url() + "#reviews")
    existing = Review.objects.filter(product=product, user=request.user).first()
    form = ReviewForm(request.POST, instance=existing)
    if not form.is_valid():
        messages.error(request, "Please choose a star rating to post your review.")
        return redirect(product.get_absolute_url() + "#reviews")
    review = form.save(commit=False)
    review.product, review.user = product, request.user
    review.verified_purchase = Order.objects.filter(
        user=request.user, status__in=[Order.Status.PAID, Order.Status.SHIPPED], items__product=product
    ).exists()
    review.save()
    messages.success(request, "Thank you! Your review has been saved.")
    return redirect(product.get_absolute_url() + "#reviews")


def _safe_next(request, fallback):
    target = request.POST.get("next") or request.META.get("HTTP_REFERER", "")
    if target and url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}):
        return target
    return fallback


@require_POST
def wishlist_toggle(request, product_id):
    wants_json = request.headers.get("x-requested-with") == "XMLHttpRequest"
    product = get_object_or_404(Product, pk=product_id, is_active=True)

    if not request.user.is_authenticated:
        login_url = reverse("accounts:login") + "?" + urlencode({"next": _safe_next(request, product.get_absolute_url())})
        if wants_json:
            return JsonResponse({"login_url": login_url}, status=401)
        return redirect(login_url)

    item, created = WishlistItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        item.delete()
    if wants_json:
        return JsonResponse({
            "wishlisted": created,
            "count": WishlistItem.objects.filter(user=request.user).count(),
        })
    messages.success(request, f"Added “{product.name}” to your wishlist." if created else "Removed from your wishlist.")
    return redirect(_safe_next(request, product.get_absolute_url()))


@login_required
def wishlist(request):
    items = WishlistItem.objects.filter(user=request.user, product__is_active=True).select_related("product")
    return render(request, "shop/wishlist.html", {"products": [i.product for i in items]})
