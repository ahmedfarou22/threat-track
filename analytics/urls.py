from django.urls import path
from . import views

urlpatterns = [
    path("assessments", views.analytics_assessments, name="analytics_assessments")
]