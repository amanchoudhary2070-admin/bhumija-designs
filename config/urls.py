from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = f"{settings.SHOP_NAME} admin"
admin.site.site_title = f"{settings.SHOP_NAME} admin"

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("account/", include("accounts.urls")),
    path("", include("shop.urls")),
    path("", include("content.urls")),
]

# Serve uploaded photos from disk in development only.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
