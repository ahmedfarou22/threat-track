from django.urls import path
from . import views

urlpatterns = [
    path("clients", views.clients, name="clients"),
    path("client/add", views.client_add, name="client_add"),
    path("client/delete", views.client_delete, name="client_delete"),
    path("clients/<int:client_id>", views.client_info, name="client_info"),
    
    path("templates", views.templates, name="templates"),
    path("template/add", views.template_add, name="template_add"),
    path("templates/delete", views.template_delete, name="template_delete"),
    path("templates/<int:template_id>", views.template_info, name="template_info"),
    path("templates/download/<int:template_id>", views.template_download, name="template_download"),
    
    path("vulnerabilities", views.vulnerabilities, name="vulnerabilities"),
    path("vulnerabilities/add", views.vulnerability_add, name="vulnerability_add"),
    path("vulnerabilities/delete", views.vulnerability_delete, name="vulnerability_delete"),
    path("vulnerabilities/<int:vulnerability_id>", views.vulnerability_info, name="vulnerability_info"),
    
]