from django.urls import path

from . import views

app_name = "webhooks"

urlpatterns = [
    path("stripe/", views.StripeWebhookView.as_view(), name="stripe-webhook"),
]
