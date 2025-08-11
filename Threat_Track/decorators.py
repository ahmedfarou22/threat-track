from django.contrib.auth.decorators import user_passes_test
from users.models import UserProfile, Role
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from functools import wraps
from assessments.models import Assessment

def has_permission_required(*permission_names):
    def decorator(view_func):
        @login_required
        def wrapped_view(request, *args, **kwargs):
            user_permissions = request.user.userprofile.role.permissions.values_list('name', flat=True)
            if not any(permission_name in user_permissions for permission_name in permission_names):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator
