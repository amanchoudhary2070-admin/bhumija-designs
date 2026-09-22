from django.urls import path

from . import views

app_name = "content"

urlpatterns = [
    path("", views.home, name="home"),
    path("newsletter/", views.newsletter_signup, name="newsletter_signup"),
    path("custom-art/", views.custom_art, name="custom_art"),
    path("contact/", views.contact, name="contact"),
    path("about/", views.about, name="about"),
    path("blog/", views.post_list, name="post_list"),
    path("blog/<slug:slug>/", views.post_detail, name="post"),
    path("pages/<slug:slug>/", views.page, name="page"),
]
