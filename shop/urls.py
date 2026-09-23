from django.urls import path

from .views import cart, catalog, checkout

app_name = "shop"

urlpatterns = [
    path("shop/", catalog.product_list, name="product_list"),
    path("new-arrivals/", catalog.new_arrivals, name="new_arrivals"),
    path("categories/", catalog.category_index, name="category_index"),
    path("category/<slug:category_slug>/", catalog.product_list, name="category"),
    path("product/<slug:slug>/", catalog.product_detail, name="product_detail"),
    path("product/<slug:slug>/review/", catalog.review_create, name="review_create"),
    path("artisans/", catalog.artisan_list, name="artisan_list"),
    path("seller/<slug:slug>/", catalog.seller_storefront, name="seller_storefront"),
    path("wishlist/", catalog.wishlist, name="wishlist"),
    path("wishlist/toggle/<int:product_id>/", catalog.wishlist_toggle, name="wishlist_toggle"),
    path("cart/", cart.cart_detail, name="cart"),
    path("cart/add/<int:product_id>/", cart.cart_add, name="cart_add"),
    path("cart/update/<int:product_id>/", cart.cart_update, name="cart_update"),
    path("cart/remove/<int:product_id>/", cart.cart_remove, name="cart_remove"),
    path("checkout/", checkout.checkout, name="checkout"),
    path("track-order/", checkout.track_order, name="track_order"),
    path("order/<uuid:public_id>/", checkout.order_detail, name="order_detail"),
    path("order/<uuid:public_id>/pay/", checkout.pay, name="pay"),
    path("order/<uuid:public_id>/razorpay/callback/", checkout.razorpay_callback, name="razorpay_callback"),
    path("order/<uuid:public_id>/dev-pay/", checkout.dev_pay, name="dev_pay"),
    path("webhooks/razorpay/", checkout.razorpay_webhook, name="razorpay_webhook"),
]
