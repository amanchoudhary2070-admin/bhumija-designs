from django.conf import settings

from .cart import Cart
from .models import Category, WishlistItem


def storefront(request):
    """Values available in every template."""
    wishlist_ids = set()
    if request.user.is_authenticated:
        wishlist_ids = set(WishlistItem.objects.filter(user=request.user).values_list("product_id", flat=True))
    return {
        "SHOP_NAME": settings.SHOP_NAME,
        "SHOP_TAGLINE": settings.SHOP_TAGLINE,
        "SHOP_EMAIL": settings.SHOP_EMAIL,
        "SHOP_PHONE": settings.SHOP_PHONE,
        "SHOP_ADDRESS": settings.SHOP_ADDRESS,
        "SOCIAL_LINKS": settings.SOCIAL_LINKS,
        "SHIPPING_FLAT_RATE": settings.SHIPPING_FLAT_RATE,
        "FREE_SHIPPING_THRESHOLD": settings.FREE_SHIPPING_THRESHOLD,
        "nav_categories": Category.objects.filter(parent=None).prefetch_related("children"),
        "cart_count": len(Cart(request)),
        "wishlist_ids": wishlist_ids,
    }
