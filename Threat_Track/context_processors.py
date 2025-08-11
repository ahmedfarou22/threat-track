def active_side_bar(request):
    app = request.path.split("/")[1] # first word in the link
    header_pill = request.path.split("/")[-1] # last word in the link

    if app == 'home':
        # this is used to get the second word of the link after the (home app) for the (dashboard and callendar)
        try:
            app = request.path.split("/")[2]
        except:
            app = 'dashboard'
    
    return {"app" : app,
            "header_pill" : header_pill}
    
    
def user_permissions(request):
    'Pass all the user permissions under the name USER_PERMISSIONS'
    if request.user.is_anonymous:
        return {"USER_PERMISSIONS": None}
    permissions = request.user.userprofile.role.permissions.values_list("name", flat=True)
    return {"USER_PERMISSIONS": permissions}