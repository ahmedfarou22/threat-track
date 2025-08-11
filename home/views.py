from Threat_Track.decorators import has_permission_required
from assessments.models import Assessment, AssessmentTask
from django.core.paginator import Paginator
from django.shortcuts import render
from django.db.models import Q
from datetime import timedelta
# Create your views here.

@has_permission_required('see_dashboard')
def dashboard(request):
    # Assessments
    user_permissions = request.user.userprofile.role.permissions.values_list('name', flat=True)
    if 'view_all_assessments' in user_permissions:
        assessments_list = Assessment.objects.all().order_by('-start_date')
        assessments_list2 = Assessment.objects.all().order_by('-start_date')
    else:
        assessments_list = Assessment.objects.filter(assigned_users=request.user).order_by('-start_date')
        assessments_list2 = Assessment.objects.filter(assigned_users=request.user).order_by('-start_date')
    paginator = Paginator(assessments_list, 4)
    assessments = paginator.get_page(request.GET.get('page'))


    closed_assessments = assessments_list.filter(status__name='Closed').count()
    in_progress_assessments = assessments_list.filter(status__name='In progress').count()
    total_vuln_found = sum(assessment.vulnerabilities.count() for assessment in assessments_list)
    tasks_assigned_to_user = AssessmentTask.objects.filter(Q(assigned_to=request.user) & ~Q(status__name='Completed')).count()
    
    index = 0
    events = []
    colors = ['#04a9f5', '#f44242', '#7cb342', '#f4a742',
              '#6d4c41', '#2196f3', '#f44336', '#673ab7']

    
    for assessment in assessments_list2:
        #color = colors[index] below line to not get index out of range
        color = colors[index % len(colors)] 
        end_date_adjusted = assessment.end_date + timedelta(days=1)
        event = {
            'url': '/assessments/' + str(assessment.id) + '/summary',
            'title': assessment.name,
            'start': assessment.start_date.strftime('%Y-%m-%d'),
            'end': end_date_adjusted.strftime('%Y-%m-%d'),
            'borderColor': color,
            'backgroundColor': color,
            'textColor': '#fff'
        }
        events.append(event)
        index += 1
    
    return render(request, 'home/index.html', {
        'assessments': assessments,
        'events': events,
        'closed_assessments': closed_assessments,
        'in_progress_assessments':in_progress_assessments,
        'total_vuln_found':total_vuln_found,
        'tasks_assigned_to_user':tasks_assigned_to_user
        }
    )

@has_permission_required('see_calendar')
def calendar(request):
    user_permissions = request.user.userprofile.role.permissions.values_list('name', flat=True)
    if 'view_all_assessments' in user_permissions:
        assessments = Assessment.objects.all().order_by('-start_date')
    else:
        assessments = Assessment.objects.filter(assigned_users=request.user).order_by('-start_date')

    index = 0
    events = []
    # colors = ['#04a9f5', '#f44242', '#7cb342']
    colors = ['#04a9f5', '#f44242', '#7cb342', '#f4a742',
              '#6d4c41', '#2196f3', '#f44336', '#673ab7']

    for assessment in assessments:
        #color = colors[index] below line to not get index out of range
        color = colors[index % len(colors)] 
        end_date_adjusted = assessment.end_date + timedelta(days=1)
        event = {
            'url': '/assessments/' + str(assessment.id) + '/summary',
            'title': assessment.name,
            'start': assessment.start_date.strftime('%Y-%m-%d'),
            'end': end_date_adjusted.strftime('%Y-%m-%d'),
            'borderColor': color,
            'backgroundColor': color,
            'textColor': '#fff'
        }
        events.append(event)
        index += 1


    return render(request, 'home/calendar.html', {'events': events})

