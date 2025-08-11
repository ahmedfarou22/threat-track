from django.urls import path
from . import views

urlpatterns = [
    path("", views.assessment_structures, name="assessment_structures"),
    path("assessment_structure_add", views.assessment_structure_add, name="assessment_structure_add"),
    path("assessment_structure_edit/<int:assessment_structure_id>", views.assessment_structure_edit, name="assessment_structure_edit"),
    path("assessment_structure_delete", views.assessment_structure_delete, name="assessment_structure_delete"),
    
    path("assessment_structure_field_edit/<int:assessment_structure_id>/<str:f_for>/<str:key>", views.assessment_structure_field_edit, name="assessment_structure_field_edit"),
    path('assessment_structure_field_delete', views.assessment_structure_field_delete, name='assessment_structure_field_delete'),
]