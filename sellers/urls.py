from django.urls import path

from . import views

app_name = "sellers"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("apply/", views.apply, name="apply"),
    path("products/", views.product_list, name="product_list"),
    path("products/new/", views.product_create, name="product_create"),
    path("products/<int:pk>/edit/", views.product_edit, name="product_edit"),
    path("products/<int:pk>/toggle/", views.product_toggle_active, name="product_toggle_active"),
    path("orders/", views.order_list, name="order_list"),
    path("orders/<int:pk>/toggle-shipped/", views.order_item_toggle_shipped, name="order_item_toggle_shipped"),
]
