from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve as serve_static

admin.site.site_header = f"{settings.SHOP_NAME} admin"
admin.site.site_title = f"{settings.SHOP_NAME} admin"

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("account/", include("accounts.urls")),
    path("sell/", include("sellers.urls")),
    path("", include("shop.urls")),
    path("", include("content.urls")),
]

# Serve uploaded photos from disk, always (not just when DEBUG=True). This is a small
# store without a CDN. Django's own django.conf.urls.static.static() helper silently
# no-ops when DEBUG=False, so it's wired up directly here with django.views.static.serve
# instead. That view isn't hardened for heavy traffic (no caching/range-request support)
# — fine for a small shop; move to S3 / Cloudflare R2 / Cloudinary before real scale.
urlpatterns += [
    re_path(r"^%s(?P<path>.*)$" % settings.MEDIA_URL.lstrip("/"), serve_static, {"document_root": settings.MEDIA_ROOT}),
]
