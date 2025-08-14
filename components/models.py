# from django.contrib.postgres.fields import JSONField
from django.db.models import JSONField
from django.contrib.auth.models import User
from django.db import models

# Create your models here.


class Client(models.Model):
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=255)
    email = models.EmailField()
    logo = models.ImageField(upload_to="clients/logos/", null=True, blank=True)
    info = models.TextField(null=True, blank=True)
    diffusion_list = JSONField(null=True, blank=True)

    def __str__(self):
        return self.name


class Vulnerability(models.Model):
    name = models.CharField(null=True, max_length=200)
    description = models.TextField(null=True, blank=True)

    tag = models.CharField(
        null=True, max_length=20
    )  # was called CVE before must be changed
    cvss = models.FloatField(null=True, blank=True)
    risk_rating = models.CharField(null=True, blank=True, max_length=20)

    impact = models.TextField(null=True, blank=True)
    remediation = models.TextField(null=True, blank=True)

    custom_fields = JSONField(null=True, blank=True)

    def __str__(self):
        return self.name


class Template(models.Model):
    name = models.CharField(max_length=50)
    about = models.TextField(null=True, blank=True)
    file = models.FileField(upload_to="templates/", null=True, blank=True)
    chart_settings = JSONField(null=True, blank=True)

    def __str__(self):
        return self.name
