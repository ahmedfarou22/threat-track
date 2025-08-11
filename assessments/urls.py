from django.urls import path
from . import views
from Threat_Track.custom_functions import calculate_cvss_31, upload_ck_image

urlpatterns = [
    path("", views.assessments, name="assessments"),
    path("assessment_add", views.assessment_add, name="assessment_add"),
    path("<int:assessment_id>/edit", views.assessment_edit, name="assessment_edit"),
    path("delete", views.assessment_delete, name="assessment_delete"),

    path("<int:assessment_id>/summary", views.assessment_summary, name="assessment_summary"),
    path("<int:assessment_id>/additional_fields", views.assessment_additional_fields, name="assessment_additional_fields"),
    path("<int:assessment_id>/vulnerabilities", views.assessment_vulnerabilities, name="assessment_vulnerabilities"),
    path("<int:assessment_id>/tasks", views.assessment_tasks, name="assessment_tasks"),
    path("<int:assessment_id>/chat_room", views.assessment_chat_room, name="assessment_chat_room"),
    path("<int:assessment_id>/attached_files", views.assessment_attached_files, name="assessment_attached_files"),
    path("<int:assessment_id>/reporting", views.assessment_reporting, name="assessment_reporting"),
    
    
    path("<int:assessment_id>/vulnerabilities/add", views.assessment_vulnerabilities_add, name="assessment_vulnerabilities_add"),
    path("<int:assessment_id>/vulnerabilities/assessment_vulnerabilities_add_froms_scan", views.assessment_vulnerabilities_add_from_scan, name="assessment_vulnerabilities_add_from_scan"),
    path("<int:assessment_id>/vulnerability/edit/<int:vulnerability_id>", views.assessment_vulnerability_edit, name="assessment_vulnerability_edit"),
    path("vulnerability/delete", views.assessment_vulnerability_delete, name="assessment_vulnerability_delete"),
    
    
    path("<int:assessment_id>/downloadfile/<int:file_id>", views.download_file, name="download_file"),
    path("deletefile", views.delete_file, name="delete_file"),
    
    path("<int:assessment_id>/tasks/add_task", views.add_task, name="add_task"),
    path("<int:assessment_id>/tasks/edit/<int:task_id>", views.edit_task, name="edit_task"),

    
    path("<int:assessment_id>/assessment_field_render_shortcodes_key/<str:f_for>/<str:key>", views.assessment_field_render_shortcodes_key, name="assessment_field_render_shortcodes_key"),
    path("<int:assessment_id>/assessment_field_edit/<str:f_for>/<str:key>", views.assessment_field_edit, name="assessment_field_edit"),
    path("assessment_field_delete", views.assessment_field_delete, name="assessment_field_delete"),
    
    # extra functions
    path("upload_ck_image", upload_ck_image, name="upload_ck_image"),
    path("calculate_cvss_31", calculate_cvss_31, name="calculate_cvss_31")
]