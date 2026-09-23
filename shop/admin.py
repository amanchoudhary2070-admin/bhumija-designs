from django.contrib import admin, messages
from django.utils.html import format_html

from .models import Artisan, Category, Order, OrderItem, Product, ProductImage, Review, SellerProfile, WishlistItem
from .services import send_shipped_email


@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = ("shop_name", "user", "phone", "product_count", "is_approved", "created_at")
    list_editable = ("is_approved",)
    list_filter = ("is_approved",)
    search_fields = ("shop_name", "user__email", "user__username", "phone")
    actions = ["approve_sellers"]

    @admin.action(description="Approve selected sellers (makes their listings public)")
    def approve_sellers(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"{updated} seller(s) approved.")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "position", "show_in_nav", "show_on_home")
    list_editable = ("position", "show_in_nav", "show_on_home")
    list_filter = ("parent",)
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("position", "name")


@admin.register(Artisan)
class ArtisanAdmin(admin.ModelAdmin):
    list_display = ("name", "village", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "village")
    prepopulated_fields = {"slug": ("name",)}


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("thumb", "name", "seller", "artisan", "price", "compare_at_price", "stock", "rating_avg", "is_featured", "is_active")
    list_display_links = ("thumb", "name")
    list_editable = ("price", "compare_at_price", "stock", "is_featured", "is_active")
    list_filter = ("is_active", "is_featured", "categories", "artisan", "seller")
    search_fields = ("name", "description", "seller__shop_name")
    filter_horizontal = ("categories",)
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("rating_avg", "rating_count")
    inlines = [ProductImageInline]

    @admin.display(description="")
    def thumb(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:48px;width:48px;object-fit:cover;border-radius:2px">', obj.image.url)
        return ""


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating", "verified_purchase", "is_approved", "created_at")
    list_editable = ("is_approved",)
    list_filter = ("is_approved", "verified_purchase", "rating")
    search_fields = ("product__name", "user__email", "title", "body")


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "created_at")
    search_fields = ("user__email", "product__name")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    fields = ("name", "unit_price", "quantity")
    readonly_fields = ("name", "unit_price", "quantity")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("reference", "created_at", "full_name", "phone", "total", "status")
    list_filter = ("status", "created_at")
    search_fields = ("email", "full_name", "phone", "payment_reference", "payment_id", "tracking_number")
    date_hierarchy = "created_at"
    inlines = [OrderItemInline]
    actions = ["mark_shipped"]

    # Money, customer and payment details are fixed once the order is placed.
    # You can change the status, courier, tracking number and your private note.
    readonly_fields = (
        "public_id", "user", "email", "full_name", "phone", "address_line1", "address_line2", "city",
        "state", "postal_code", "country", "subtotal", "shipping", "total",
        "payment_provider", "payment_reference", "payment_id", "created_at", "paid_at",
    )
    fieldsets = (
        ("Order", {"fields": ("status", "courier", "tracking_number", "internal_note", "public_id", "created_at", "paid_at")}),
        ("Customer", {"fields": ("user", "full_name", "email", "phone")}),
        ("Ship to", {"fields": ("address_line1", "address_line2", "city", "state", "postal_code", "country")}),
        ("Payment", {"fields": ("subtotal", "shipping", "total", "payment_provider", "payment_reference", "payment_id")}),
    )

    def has_add_permission(self, request):
        return False

    @admin.action(description="Mark as shipped and email the customer")
    def mark_shipped(self, request, queryset):
        sent = 0
        for order in queryset.filter(status=Order.Status.PAID):
            order.status = Order.Status.SHIPPED
            order.save(update_fields=["status"])
            try:
                send_shipped_email(order)
            except Exception as exc:
                self.message_user(request, f"Order {order.reference} marked shipped, but the email failed: {exc}", messages.WARNING)
            sent += 1
        skipped = queryset.count() - sent
        self.message_user(request, f"{sent} order(s) marked as shipped.")
        if skipped:
            self.message_user(request, f"{skipped} skipped (only confirmed orders can be shipped).", messages.WARNING)
