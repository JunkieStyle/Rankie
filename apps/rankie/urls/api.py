from django.urls import path, include
from rest_framework.routers import DefaultRouter

import apps.rankie.views as views

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r"gameresults", views.GameResultViewSet, basename="gameresults")

# The API URLs are now determined automatically by the router.
app_name = "rankie"

urlpatterns = [
    path("", include(router.urls)),
]
