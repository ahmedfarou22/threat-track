from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.decorators import login_required
from Threat_Track.decorators import has_permission_required 
from django.core.paginator import Paginator
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from .models import Activity

@has_permission_required('see_activities')
def activities(request):  
    query = request.GET.get('q')
    if query:
        activities = Activity.objects.filter(
            Q(user__username__icontains=query) | 
            Q(event__icontains=query) | 
            Q(date__icontains=query)
        ).order_by('-date')
    else:
        activities = Activity.objects.all().order_by('-date')
        
    paginator = Paginator(activities, 10)  # Show 10 events per page
    activities_to_show = paginator.get_page(request.GET.get('page'))
    
    return render(request, 'activities/activities.html',{
        "activities": activities_to_show})


def add_activity(request,event):
        max_update_time = timezone.now() - timedelta(days=30)  # Set the maximum update time to 1 month ago
        Activity.objects.filter(date__lt=max_update_time).delete()  # Delete outdated activities
        Activity.objects.create(user=request.user, event=event)
        messages.success(request, event)