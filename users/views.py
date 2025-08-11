from django.contrib.auth.password_validation import CommonPasswordValidator
from django.shortcuts import render, get_object_or_404, redirect
from Threat_Track.decorators import has_permission_required
from django.contrib.auth.decorators import login_required
from .models import UserProfile, Role, Team, Permission
from Threat_Track.custom_functions import resize_image
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User, auth
from Threat_Track.validations import Validation
from django.contrib.auth import authenticate
from django.core.paginator import Paginator
from axes.decorators import axes_dispatch
from activities.views import add_activity
from django.db.models import Case, When
from django.contrib.auth import logout
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q
import os

################# access control notes only a manger can view, add, edit, or change password for users (@has_permission_required('w_users')) ############## 
@has_permission_required('w_users')
def users_all(request):
    query = request.GET.get('q')
    selected_role = request.GET.get('roles')
    users_list = User.objects.all().order_by(
        Case(
            When(userprofile__role__name='Manager', then=1),
            When(userprofile__role__name='Team Lead', then=2),
            When(userprofile__role__name='Pentester', then=3),
            When(userprofile__role__name='Guest', then=4),
            default=5,
        )
    )


    if selected_role:
        users_list = users_list.filter(userprofile__role__name=selected_role)


    if query:
        users_list = users_list.filter(
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query) | 
            Q(email__icontains=query) | 
            Q(username__icontains=query) | 
            Q(userprofile__phone_number__icontains=query) 
        )

    
    paginator = Paginator(users_list, 10)
    users_to_show = paginator.get_page(request.GET.get('page'))
    

    return render(request, 'users/users_all.html',{'users_list':users_to_show,
                                                   'user_roles':Role.objects.all(),
                                                   'selected_roles':selected_role})

@has_permission_required('w_users')
def user_add(request):
    if request.method == 'POST':
        # Get form data
        first_name = Validation.validate_first_last_name(request.POST['first_name'])
        last_name = Validation.validate_first_last_name(request.POST['last_name'])
        phone_number = Validation.validate_phoneNumber(request.POST['phone_number'])
        email = Validation.validate_email(request.POST['email'])
        role = Validation.validate_object(Role, request.POST['role'])
        
        got_username = Validation.validate_username(request.POST['username'])
        password = Validation.validate_password(request.POST['password'])
        

        # Create new user object
        user = User.objects.create_user(
            username=got_username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        
        user_profile = UserProfile(
                user=user,
                phone_number=phone_number,
                role=role
            )

        
        # if Profile pic then validate, resize, update
        if request.FILES:
            profile_picture = Validation.validate_image(request.FILES.get('profile_picture'))
            user_profile.profile_pic = resize_image(profile_picture, str(user.username) + str(user.id), 500, 500)
        
        user.save()
        user_profile.save()
        
        add_activity(request,"User added  : " + str(got_username))
        return redirect('users_all')
    else:
        return render(request, 'users/user_add.html', {'user_roles': Role.objects.all()})

@has_permission_required('w_users')
def user_edit(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user_profile = UserProfile.objects.get(user=user)
    
    if request.method == 'POST':
        user.first_name = Validation.validate_first_last_name(request.POST['first_name'])
        user.last_name = Validation.validate_first_last_name(request.POST['last_name'])
        user.email = Validation.validate_email(request.POST['email'])
        user.username = Validation.validate_editedUsername(request.POST['username'], user.username)
        user_profile.phone_number = Validation.validate_phoneNumber(request.POST['phone_number'])
        user_profile.role = Validation.validate_object(Role, request.POST['role'])
        
        if request.FILES:
            new_validated_img = Validation.validate_image(request.FILES.get('profile_picture')) 
            # delete old image if any
            if user_profile. profile_pic:
                user_profile. profile_pic.delete()
            user_profile.profile_pic = resize_image(new_validated_img, str(user.username) + str(user.id), 500, 500)
        
        user_profile.save()
        user.save()
        
        
        add_activity(request,"User edited  : " + str(user))
        return redirect('users_all')
    else:
        return render(request, 'users/user_edit.html', {'user_roles': Role.objects.all(),'user':user})

@has_permission_required('w_users')
def user_delete(request):
    user_id = request.POST.get('user_id')
    
    user = get_object_or_404(User, id=user_id)
    user_profile = user.userprofile
    profile_pic = user.userprofile.profile_pic
    
    if user_profile.role.name == 'Manager':
        manager_count = User.objects.filter(userprofile__role__name='Manager').count()
        # Check if the user is the last "Manager"
        if manager_count <= 1:
            messages.error(request, 'Cannot delete the last Manager')
            return redirect('users_all')
    
    if profile_pic:
        profile_pic.delete()
    user.delete()
    
    add_activity(request,"User deleted  : " + str(user))
    return redirect('users_all')



# ------------------------------------ Teams ------------------------------------
@has_permission_required('w_users')
def teams_all(request):
    teams_list = Team.objects.all().order_by("-id")
    
    query = request.GET.get('q')
    selected_user = request.GET.get('selected_user')

    if selected_user:
        teams_list = teams_list.filter(users__username=selected_user)
    if query:
        teams_list = teams_list.filter(name__icontains=query)
    
    paginator = Paginator(teams_list, 10)
    teams_to_show = paginator.get_page(request.GET.get('page'))

    return render(request, 'users/teams_all.html',{'teams_list':teams_to_show,
                                                   'users_all':User.objects.all(),
                                                   'selected_user':selected_user
                                                   })

@has_permission_required('w_users')
def teams_add(request):
        users_all = User.objects.all().order_by(
        Case(
            When(userprofile__role__name='Manager', then=1),
            When(userprofile__role__name='Team Lead', then=2),
            When(userprofile__role__name='Pentester', then=3),
            When(userprofile__role__name='Guest', then=4),
            default=5,
        )
    )
        if request.method == 'POST':
            name = Validation.validate_unique_name(Team, request.POST['teams_name'])
            description = request.POST['description']
            assigned_users = Validation.validate_many_objects(User, request.POST.getlist('assigned_users'))
            team_to_add = Team.objects.create(name=name, description=description)
            
            team_to_add.users.set(assigned_users)
            team_to_add.save()
            
            add_activity(request, "Team added : " + str(name))
            return redirect('teams_all')
        
        else:
            return render(request, 'users/teams_add.html',{'users_all':users_all,
            })

@has_permission_required('w_users')
def teams_edit(request,team_id):
    users_all = User.objects.all()
    team_to_edit = get_object_or_404(Team, id=team_id)
    users_sorted = sorted(users_all, key=lambda user: user in team_to_edit.users.all(), reverse=True)
    
    if request.method == 'POST':
        team_to_edit.name = Validation.validate_edited_unique_name(Team, request.POST['teams_name'], team_to_edit.name)
        team_to_edit.description = request.POST['description']
        team_to_edit.users.set(Validation.validate_many_objects(User, request.POST.getlist('assigned_users')))
        team_to_edit.save()
        
        add_activity(request, "Team Edited  : " + str(team_to_edit))
        return redirect('teams_all')
    
    else:
        return render(request, 'users/teams_edit.html',{'users_all':users_sorted,
                                                    'team_to_edit':team_to_edit
            })

@has_permission_required('w_users')
def teams_delete(request):
    team_id = request.POST.get('team_id')
    
    team_to_delete = get_object_or_404(Team, id=team_id)
    team_to_delete.delete()
    
    add_activity(request, "Team deleted  : " + str(team_to_delete))
    return redirect('teams_all')

# Ajax functions
@has_permission_required('edit_assessments', 'add_assessments')
def laod_team(request):
    if request.method == 'GET':
        team_id = request.GET.get('team_id')
        if team_id:
            try:
                team = Team.objects.get(id=team_id)
                users = team.users.all().values('id', 'username', 'first_name', 'last_name')
                return JsonResponse({'status': 'success', 'users': list(users)})
            except Team.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Team does not exist'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid request'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


# ------------------------------------ Roles ------------------------------------
@has_permission_required('w_users')
def roles_all(request):
    roles_list = Role.objects.all()
    query = request.GET.get('q')
    if query:
        roles_list = roles_list.filter(name__icontains=query)
    
    paginator = Paginator(roles_list, 10)
    roles_to_show = paginator.get_page(request.GET.get('page'))
    
    return render(request, 'users/roles_all.html',{'roles_list':roles_to_show})

@has_permission_required('w_users')
def role_add(request):
    if request.method == 'POST':
        name = Validation.validate_unique_name(Role, request.POST['role_name'])
        description = request.POST['description']
        color = Validation.validate_color(request.POST['color'])
        
        role = Role(
            name=name,
            description=description,
            color=color
        )
        role.save()
        
        # Permissions 
        permissions = Validation.validate_permissions(Permission, [request.POST['assessments_access'],request.POST['assessment_summary'],
                       request.POST['assessment_additional_fields'],request.POST['assessment_vulnerabilities'],
                       request.POST['assessment_attached_files'],request.POST['assessment_tasks'],request.POST['assessment_chat_room'],
                       request.POST['dashboard'],request.POST['calendar'],request.POST['analytics'],request.POST['activites'],
                       request.POST['clients'],request.POST['templates'],request.POST['vulnerabilities'],
                       request.POST['assessment_structures'],request.POST['users_teams_roles']])
        
        # Add more permissions from cheak box
        permissions.append(Validation.validate_permission(Permission,request.POST['add_assessments'])) if 'add_assessments' in request.POST else None
        permissions.append(Validation.validate_permission(Permission,request.POST['edit_assessments'])) if 'edit_assessments' in request.POST else None
        permissions.append(Validation.validate_permission(Permission,request.POST['delete_assessments'])) if 'delete_assessments' in request.POST else None
        permissions.append(Validation.validate_permission(Permission,request.POST['generate_report'])) if 'generate_report' in request.POST else None
        
        
        for permission in permissions:
            if permission != "":
                role.permissions.add(Permission.objects.get(name=permission))
                if permission.startswith('w_'):
                    role.permissions.add(Permission.objects.get(name='r' + permission[1:]))

        role.save()
        add_activity(request,"Role added  : " + str(name))
        return redirect('roles_all')
    
    else:
        return render(request, 'users/role_add.html')


@has_permission_required('w_users')
def role_edit(request,role_id):
    role_to_edit = get_object_or_404(Role, id=role_id)
    if request.method == 'POST':
        name = Validation.validate_edited_unique_name(Role, request.POST['role_name'], role_to_edit.name)
        if role_to_edit.name == 'Manager':
            messages.error(request, "Cannot edit the Manager")
            return redirect('roles_all') 
            
        description = request.POST['description']
        color = Validation.validate_color(request.POST['color'])
        
        role_to_edit.name = name
        role_to_edit.description = description
        role_to_edit.color = color
        
        
        # Permissions 
        permissions = Validation.validate_permissions(Permission, [request.POST['assessments_access'],request.POST['assessment_summary'],
                       request.POST['assessment_additional_fields'],request.POST['assessment_vulnerabilities'],
                       request.POST['assessment_attached_files'],request.POST['assessment_tasks'],request.POST['assessment_chat_room'],
                       request.POST['dashboard'],request.POST['calendar'],request.POST['analytics'],request.POST['activites'],
                       request.POST['clients'],request.POST['templates'],request.POST['vulnerabilities'],
                       request.POST['assessment_structures'],request.POST['users_teams_roles']])
        
        # Add more permissions from cheak box
        permissions.append(Validation.validate_permission(Permission,request.POST['add_assessments'])) if 'add_assessments' in request.POST else None
        permissions.append(Validation.validate_permission(Permission,request.POST['edit_assessments'])) if 'edit_assessments' in request.POST else None
        permissions.append(Validation.validate_permission(Permission,request.POST['delete_assessments'])) if 'delete_assessments' in request.POST else None
        permissions.append(Validation.validate_permission(Permission,request.POST['generate_report'])) if 'generate_report' in request.POST else None
        
        role_to_edit.permissions.clear()
        for permission in permissions:
            if permission != "":
                role_to_edit.permissions.add(Permission.objects.get(name=permission))
                if permission.startswith('w_'):
                    role_to_edit.permissions.add(Permission.objects.get(name='r' + permission[1:]))

        role_to_edit.save()

        add_activity(request,"Role edited  : " + str(name))
        return redirect('roles_all')
    
    else:
        role_to_edit_permissions = list(role_to_edit.permissions.values_list('name', flat=True))
        return render(request, 'users/role_edit.html',{'role_to_edit':role_to_edit,'role_to_edit_permissions':role_to_edit_permissions})
    

@has_permission_required('w_users')
def role_delete(request):
    role_id = request.POST.get('role_id')
    role_to_delete = get_object_or_404(Role, id=role_id)
    
    if User.objects.filter(userprofile__role=role_to_delete):
        messages.error(request, "Cannot delete role with users")
        return redirect('roles_all')
    
    elif role_to_delete.name == 'Manager':
        messages.error(request, "Cannot delete the manager role")
        return redirect('roles_all')
    
    else:
        role_to_delete.delete()
        add_activity(request,"Role deleted  : " + str(role_to_delete))
        return redirect('roles_all')



# ------------------------------------ Extra for login/logout system ------------------------------------

@axes_dispatch
def login_user(request):
    if request.user.is_authenticated:
        messages.warning(request, 'You are already signed in')
        return redirect('/home/dashboard')
    
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(request,username=username, password=password)

        if user:
            auth.login(request, user)
            return redirect('/home/dashboard')
        else:
            messages.warning(request, 'Invalid Username or Password')
            return redirect('login_user')

    else:
        return render(request, 'users/login.html')
    
def logout_user(request):
    logout(request)
    messages.success(request, 'Logout Successful')
    return redirect('/users/login')

def lockout(request,credentials):
     return render(request, 'users/lockout.html')
 
 
@login_required
def profile(request):
    user = get_object_or_404(User, id=request.user.id)
    user_profile = UserProfile.objects.get(user=user)
    
    if request.method == 'POST':
        user_profile.phone_number = Validation.validate_phoneNumber(request.POST['phone_number'])
        
        if request.FILES:
            new_validated_img = Validation.validate_image(request.FILES.get('profile_picture'))
            if user_profile.profile_pic:
                user_profile.profile_pic.delete()
            user_profile.profile_pic = resize_image(new_validated_img, str(user.username) + str(user.id), 500, 500)
        
        user_profile.save()
        user.save()
        
        add_activity(request,"User profile updated  : " + str(user))
        return redirect('dashboard')
    else:
        return render(request, 'users/profile.html')



@login_required
def user_changepass(request):
    user = request.user
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = Validation.validate_password(request.POST.get('new_password'))
        
        user_authenticated = authenticate(request=request, username=user.username, password=old_password)
        if not user_authenticated:
            messages.error(request, "Incorrect old password. Please try again.")
            return redirect('user_changepass')

        elif user_authenticated:
            user.set_password(new_password)
            user.save()
            add_activity(request, "User changed password: " + str(user))
            return redirect('users_all')

    return render(request, 'users/user_changepass.html', {'user': user})

@has_permission_required('w_users')
def admin_changepass(request,user_id):
    admin = request.user
    user_to_change_pass = Validation.validate_object(User, user_id)
    if request.method == 'POST':
        admin_password = request.POST.get('admin_password')
        new_password = Validation.validate_password(request.POST.get('new_password'))
        
        user_authenticated = authenticate(request=request, username=admin.username, password=admin_password)
        if not user_authenticated:
            messages.error(request, "Your password is incorrect. Please try again.")
            return redirect('admin_changepass', user_id=user_id)

        elif user_authenticated:            
            user_to_change_pass.set_password(new_password)
            user_to_change_pass.save()
            add_activity(request, "Admin changed password: " + str(user_to_change_pass))
            return redirect('users_all')

    return render(request, 'users/admin_changepass.html', {'user_to_change_pass': user_to_change_pass})


#Check names Ajax function
@has_permission_required('w_users')
def check_name_availability(request):
    if request.method == 'GET':
        model = request.GET.get('model')
        name = request.GET.get('name')
        model_dict = {'user': User,
                      'team':Team,
                      'role': Role
                      }
        if name and model in model_dict:
            try:
                model_dict[model].objects.get(username=name) if model == 'user' else model_dict[model].objects.get(name=name)
                return JsonResponse({'status': 'error', 'message': 'Username already exists'})
            except User.DoesNotExist:
                return JsonResponse({'status': 'success', 'message': 'Username is available'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid request'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
