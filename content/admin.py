from django.contrib import admin

from .models import Banner, ContactMessage, CustomArtRequest, Page, Post, Subscriber


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ("placement", "title", "position", "is_active")
    list_editable = ("position", "is_active")
    list_filter = ("placement", "is_active")


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_published", "updated_at")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "is_published", "published_at")
    list_filter = ("is_published",)
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "published_at"


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "created_at")
    search_fields = ("email",)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "subject", "is_handled", "created_at")
    list_editable = ("is_handled",)
    list_filter = ("is_handled",)
    search_fields = ("name", "email", "subject", "message")


@admin.register(CustomArtRequest)
class CustomArtRequestAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "budget", "status", "created_at")
    list_editable = ("status",)
    list_filter = ("status", "budget")
    search_fields = ("name", "email", "description")
