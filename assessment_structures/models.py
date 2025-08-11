from django.db import models
from django.db.models import JSONField

# Create your models here.
class Assessment_Structure(models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=100,null=True, blank=True)
    
    s_fields = JSONField(null=True, blank=True)
    a_fields = JSONField(null=True, blank=True)
    v_fields = JSONField(null=True, blank=True)

    def __str__(self):
        return self.name