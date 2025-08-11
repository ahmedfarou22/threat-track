from django.contrib import admin
from .models import Assessment, AssessmentStatus, AssessmentPriority, AssessmentFile, TaskStatus
from .models import AssessmentVulnerability, VulnerabilityScreenshot, ChatMessage , CKImageUpload, AssessmentTask

# Register your models here.
admin.site.register(Assessment)
admin.site.register(AssessmentStatus)
admin.site.register(AssessmentPriority)
admin.site.register(AssessmentFile)
admin.site.register(TaskStatus)


admin.site.register(AssessmentVulnerability)
admin.site.register(VulnerabilityScreenshot)
admin.site.register(AssessmentTask)


admin.site.register(ChatMessage)
admin.site.register(CKImageUpload)
