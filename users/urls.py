from django.urls import path
from . import views

urlpatterns = [
    path("users", views.users_all, name="users_all"),
    path("user_add", views.user_add, name="user_add"),
    path("user_delete", views.user_delete, name="user_delete"),
    path("<int:user_id>/edit", views.user_edit, name="user_edit"),
    path("check_name_availability", views.check_name_availability, name="check_name_availability"),
    
    
    path("teams", views.teams_all, name="teams_all"),
    path("teams_add", views.teams_add, name="teams_add"),
    path("teams_delete", views.teams_delete, name="teams_delete"),
    path("team/<int:team_id>/edit", views.teams_edit, name="teams_edit"),
    path("load_team/",views.laod_team,name="load_team"),
    
    path("roles", views.roles_all, name="roles_all"),
    path("role_add", views.role_add, name="role_add"),
    path("role_delete", views.role_delete, name="role_delete"),
    path("role/<int:role_id>/edit", views.role_edit, name="role_edit"),
    
    path("profile", views.profile, name="profile"),
    path("login", views.login_user, name="login_user"),
    path("logout", views.logout_user, name="logout_user"),
    
    path("user_changepass", views.user_changepass, name="user_changepass"),
    path("admin_changepass/<int:user_id>", views.admin_changepass, name="admin_changepass")
    
    
]