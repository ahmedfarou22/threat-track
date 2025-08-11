from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, null=True ,on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=64)
    role = models.ForeignKey('Role', on_delete=models.SET_NULL, null=True)
    profile_pic = models.ImageField(upload_to='profile_pics', blank=True,null=True)
    
    def __str__(self) -> str:
        return(self.user.username)


class Role(models.Model):
    name = models.CharField(max_length=64)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default="#04a9f5")
    
    permissions = models.ManyToManyField('Permission')
    
    def __str__(self):
        return self.name

class Permission(models.Model):
    name = models.CharField(max_length=200,blank=True,null=True)
    for_app = models.CharField(max_length=200,blank=True,null=True)
    
    def __str__(self):
        return self.name


class Team(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    users = models.ManyToManyField(User, related_name='teams')

    def __str__(self):
        return self.name
    
