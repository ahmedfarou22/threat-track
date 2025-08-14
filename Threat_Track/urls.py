"""Threat_Track URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf.urls.static import static
from django.urls import path, include
from django.shortcuts import render
from django.contrib import admin
from django.conf import settings
from django.http import JsonResponse


# Health check endpoint for Docker
def health_check(request):
    """Simple health check for Docker containers"""
    return JsonResponse(
        {
            "status": "healthy",
            "service": "Threat Track",
            "storage_type": getattr(settings, "MEDIA_STORAGE_TYPE", "LOCAL"),
        }
    )


urlpatterns = [
    path("health/", health_check, name="health_check"),  # Health check for Docker
    path(
        "5cdba533cc0c408b1d7bb5e8c9b00b01b691e3e25cdba533cc0c408b1d7bb5e8c9b00b01b691e3e2/",
        admin.site.urls,
    ),  # SHA1_Hash(threat-track/admin) * 2 = 5cdba533cc0c408b1d7bb5e8c9b00b01b691e3e2
    path("", include("home.urls")),
    path("home", include("home.urls")),
    path("home/", include("home.urls")),
    path("assessments/", include("assessments.urls")),
    path("analytics/", include("analytics.urls")),
    path("activities/", include("activities.urls")),
    path("components/", include("components.urls")),
    path("assessment_structures/", include("assessment_structures.urls")),
    path("users/", include("users.urls")),
]

urlpatterns.append(path("admin/", admin.site.urls)) if settings.DEBUG else None

# To serve media files from the server itself (not secure + not for production)
if settings.MEDIA_STORAGE_TYPE == "LOCAL":
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# Custom erorr pages
def custom_403(request, exception):
    return render(request, "home/page-403.html", status=403)


def custom_404(request, exception):
    return render(request, "home/page-404.html", status=404)


def custom_500(request):
    return render(request, "home/page-500.html", status=500)


handler403 = custom_403
handler404 = custom_404
handler500 = custom_500
