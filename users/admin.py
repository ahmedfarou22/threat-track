from django.contrib import admin
from .models import UserProfile, Role, Team,Permission

admin.site.register(UserProfile)
admin.site.register(Role)
admin.site.register(Team)
admin.site.register(Permission)