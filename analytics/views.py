
from assessments.models import Assessment, AssessmentStatus, AssessmentPriority, AssessmentVulnerability
from Threat_Track.decorators import has_permission_required
from components.models import Client, Vulnerability
from django.contrib.auth.models import User
from django.db.models import Min, Max
from django.shortcuts import render
import json

@has_permission_required('see_analytics')
def analytics_assessments(request):
    # 1. Get Selected Filters
    selected_clients = request.GET.getlist('selected_clients')
    client_ids = [int(client_id) for client_id in selected_clients]
    selected_from_date = request.GET.get('selected_from_date')
    selected_to_date = request.GET.get('selected_to_date')
    selected_status = request.GET.get('selected_status')
    selected_priority = request.GET.get('selected_priority')
    selected_created_by = request.GET.getlist('selected_created_by')
    selected_created_by_ids = [int(user_id) for user_id in selected_created_by]
    selected_assigned_to = request.GET.getlist('selected_assigned_to')
    selected_assigned_to_ids = [int(user_id) for user_id in selected_assigned_to]
    selected_risk_rating = request.GET.get('selected_risk_rating')
    
    # 2. Filter Section
    filtered_assessments = Assessment.objects.all()
    if selected_clients:
        filtered_assessments = filtered_assessments.filter(client__id__in=client_ids)
    if selected_from_date:
        filtered_assessments = filtered_assessments.filter(start_date__gte=selected_from_date)
    if selected_to_date:
        filtered_assessments = filtered_assessments.filter(end_date__lte=selected_to_date)

    if selected_status is not None and selected_status != "":
            filtered_assessments = filtered_assessments.filter(status__name=selected_status)
    
    if selected_priority is not None and selected_priority != "":
        filtered_assessments = filtered_assessments.filter(priority__name=selected_priority)
    
    if selected_priority:
        filtered_assessments = filtered_assessments.filter(who_created__id__in=selected_created_by_ids)
    
    if selected_assigned_to_ids:
        filtered_assessments = filtered_assessments.filter(assigned_users__id__in=selected_assigned_to_ids).distinct()
    
    filtered_vulnerabilities = AssessmentVulnerability.objects.filter(assessment__in=filtered_assessments)
    if selected_risk_rating and selected_risk_rating != "0":
        filtered_vulnerabilities = filtered_vulnerabilities.filter(risk_rating=selected_risk_rating)
        filtered_assessments_ids = filtered_vulnerabilities.values_list('assessment', flat=True).distinct()
        filtered_assessments = Assessment.objects.filter(pk__in=filtered_assessments_ids)
    
    # 3. Results to show
    first_creation_time = filtered_assessments.aggregate(Min('start_date'))['start_date__min']
    latest_end_date = filtered_assessments.aggregate(Max('end_date'))['end_date__max']
    client_to_show = Client.objects.filter(id__in=filtered_assessments.order_by().values_list('client__id', flat=True).distinct())
    created_by_to_show = User.objects.filter(id__in=filtered_assessments.order_by().values_list('who_created__id', flat=True).distinct())
    assigned_users_to_show = User.objects.filter(id__in=filtered_assessments.values_list('assigned_users__id', flat=True).distinct())
    
    
    # -----------------------------  Graphs  -----------------------------
    # Assessment Statuses Graph
    assessment_statuses = filtered_assessments.values_list('status__name', flat=True).distinct()
    assessment_statuses_graph_to_show = []
    for status in assessment_statuses:
        count = filtered_assessments.filter(status__name=status).count()
        assessment_statuses_graph_to_show.append({'value': count, 'label': status})
    
    # Vulnerabilites Risk Rating Graph
    vulnerability_risk_rating = filtered_vulnerabilities.values_list('risk_rating', flat=True).distinct()
    vulnerability_risk_rating_graph_to_show = []
    for risk_rating in vulnerability_risk_rating:
        count = filtered_vulnerabilities.filter(risk_rating=risk_rating).count()
        vulnerability_risk_rating_graph_to_show.append({'value': count, 'label': risk_rating})
    
    # Assessment Priority Graph
    assessment_priorities = filtered_assessments.values_list('priority__name', flat=True).distinct()
    assessment_priorities_data = {}
    for priority in assessment_priorities:
        priority_count = filtered_assessments.filter(priority__name=priority).count()
        assessment_priorities_data[priority] = priority_count
    assessment_priorities_graph_to_show = []
    for priority, count in assessment_priorities_data.items():
        assessment_priorities_graph_to_show.append({'y': priority, 'a': count})


    # -----------------------------  Context to Load  ----------------------------- 
    context = {
    'assessments_all' : Assessment.objects.all().count(),
    'Vulnerabilities_all': AssessmentVulnerability.objects.all().count(),
    'clients_all' : Client.objects.all(),
    'users_all' : User.objects.all(),
    'assessment_statuses_all' : AssessmentStatus.objects.all(),
    'assessment_priorities_all' : AssessmentPriority.objects.all(),
    
    'selected_clients': client_ids,
    'selected_from_date': selected_from_date,
    'selected_to_date': selected_to_date,
    'selected_status':selected_status,
    'selected_priority': selected_priority,
    'selected_created_by':selected_created_by_ids,
    'selected_assigned_to': selected_assigned_to_ids,
    'selected_risk_rating':selected_risk_rating,
    
    'total_filtered_assessments_to_show': filtered_assessments.count(),
    'total_filtered_vulnerabilities_to_show':filtered_vulnerabilities.count(),
    'precent_for_bar': (filtered_assessments.count() / Assessment.objects.all().count()) * 100 if Assessment.objects.all().count() > 0 else None ,
    'first_creation_time_to_show':first_creation_time,
    'latest_end_date_to_show':latest_end_date,
    'client_to_show':client_to_show,
    'created_by_to_show':created_by_to_show,
    'assigned_users_to_show':assigned_users_to_show,
    'assessment_statuses_graph_to_show': json.dumps(assessment_statuses_graph_to_show),
    'vulnerability_risk_rating_graph_to_show':json.dumps(vulnerability_risk_rating_graph_to_show),
    'assessment_priorities_graph_to_show': assessment_priorities_graph_to_show
    }
    
    return render(request, 'analytics/analytics_assessments.html',context)
