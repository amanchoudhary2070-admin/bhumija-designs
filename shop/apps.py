from django.apps import AppConfig


class ShopConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "shop"

    def ready(self):
        from . import signals  # noqa: F401  (keeps product ratings in sync with reviews)
