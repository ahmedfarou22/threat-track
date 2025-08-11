from django.db import models
from django.contrib.auth.models import User
from components.models import Client, Template
# from django.contrib.postgres.fields import JSONField
from django.db.models import JSONField

class Assessment(models.Model):
    name = models.CharField(max_length=255,null=True, blank=True)

    creation_date = models.DateTimeField(auto_now=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True, related_name='assessments')
    priority = models.ForeignKey('AssessmentPriority', on_delete=models.SET_NULL, null=True, blank=True)
    who_created = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_assessments')
    status = models.ForeignKey('AssessmentStatus', on_delete=models.SET_NULL, null=True, blank=True)
    
    assigned_users = models.ManyToManyField(User, related_name='assigned_assessments', blank=True)

    vulnerabilities = models.ManyToManyField('AssessmentVulnerability', related_name='vulnerabilities_assessments', blank=True)
    
    files = models.ManyToManyField('AssessmentFile', related_name='assessments', blank=True)
    tasks = models.ManyToManyField('AssessmentTask', related_name='assessments', blank=True)

    
    # for dynamic fileds (Assessment structure)
    af_name = models.CharField(max_length=255,null=True, blank=True)
    s_fields = JSONField(null=True, blank=True)
    a_fields = JSONField(null=True, blank=True)
    v_fields = JSONField(null=True, blank=True)
    
    def __str__(self):
        return str(self.name)

class AssessmentPriority(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return str(self.name)

# Assessment Attahed files
class AssessmentFile(models.Model):
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='assessment_files/')
    added_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class AssessmentStatus(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return str(self.name)

# Assessment Vulnerabilities
class AssessmentVulnerability(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='vulnerabilities_w') 
    number = models.PositiveIntegerField(default=1)
    status = models.CharField(null=True,blank=True,max_length=20) #
    target = models.CharField(max_length=200, null=True, blank=True)
    
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    
    tag = models.CharField(null=True,blank=True, max_length=20) 
    cvss = models.FloatField(null=True, blank=True)
    risk_rating = models.CharField(null=True, blank=True, max_length=20) 

    impact = models.TextField(null=True, blank=True)
    remediation = models.TextField(null=True, blank=True)
    
    poc_text = models.TextField(null=True, blank=True)
    poc_screenshots = models.ManyToManyField('VulnerabilityScreenshot', related_name='vulnerabilities', blank=True)

    fields = JSONField(null=True, blank=True)
    
    def __str__(self):
        return self.name

class VulnerabilityScreenshot(models.Model):
    vulnerability = models.ForeignKey(AssessmentVulnerability, on_delete=models.CASCADE, related_name='screenshots')
    image = models.ImageField(upload_to='vulnerabilityscreenshot/')
    
    def __str__(self):
        return self.image.name

# Assessment Chat Messages
class ChatMessage(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return str(self.assessment) + str(self.message)
    

# Tasks
class AssessmentTask(models.Model):
    task = models.TextField(null=True)
    assigned_to = models.ManyToManyField(User, related_name='assigned_tasks', blank=True)
    status = models.ForeignKey('TaskStatus', on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return self.task

class TaskStatus(models.Model):
    name = models.CharField(max_length=50)
    
    def __str__(self):
        return self.name
    
# Custom CK 
class CKImageUpload(models.Model):
    image = models.ImageField(upload_to='ck_image_uploads/')
    created_at = models.DateTimeField(auto_now_add=True)
    
    for_model = models.TextField(null=True, blank=True)
    model_id = models.PositiveIntegerField(null=True, blank=True)
