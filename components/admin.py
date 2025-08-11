from django.contrib import admin
from .models import Client, Vulnerability, Template

admin.site.register(Client)
admin.site.register(Vulnerability)
admin.site.register(Template)