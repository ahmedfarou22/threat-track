from django.shortcuts import render, redirect, get_object_or_404
from Threat_Track.decorators import has_permission_required
from django.contrib.auth.decorators import login_required
from .models import Client, Vulnerability, Template
from django.core.exceptions import PermissionDenied
from Threat_Track.validations import Validation
from django.core.paginator import Paginator
from activities.views import add_activity
from django.http import FileResponse, HttpResponse
from django.contrib import messages
import json
from wsgiref.util import FileWrapper
from django.core.files import File
from django.db.models import Q
from io import BytesIO
import io, json

# ============================================== Clients ========================================


@has_permission_required("r_clients")
def clients(request):
    query = request.GET.get("q")
    if query:
        client_list = Client.objects.filter(
            Q(name__icontains=query)
            | Q(email__icontains=query)
            | Q(phone_number__icontains=query)
        )
    else:
        client_list = Client.objects.all()

    paginator = Paginator(client_list, 10)  # Show 10 clients per page
    clients = paginator.get_page(request.GET.get("page"))
    return render(request, "components/clients/client_all.html", {"clients": clients})


@has_permission_required("r_clients")
def client_info(request, client_id):
    client = Client.objects.get(id=client_id)

    if request.method == "POST":
        try:
            user_permissions = request.user.userprofile.role.permissions.values_list(
                "name", flat=True
            )
            if "w_clients" not in user_permissions:
                raise PermissionDenied

            print(f"DEBUG: Editing client {client_id}")
            print(f"DEBUG: POST data: {dict(request.POST)}")

            client.name = Validation.validate_name(request.POST.get("client_name"))
            client.email = Validation.validate_notRequired_email(
                request.POST.get("client_email")
            )
            client.phone_number = Validation.validate_notRequired_phoneNumber(
                request.POST.get("client_phone_number")
            )
            client.info = request.POST.get("client_info")

            # Handle diffusion list data
            client.diffusion_list = handle_diffusion_list(request)

            if request.FILES and "client_logo" in request.FILES:
                validated_image = Validation.validate_image(
                    request.FILES["client_logo"]
                )
                # delete old logo if any
                if client.logo:
                    client.logo.delete()
                client.logo = validated_image

            client.save()
            print(f"DEBUG: Updated client with diffusion_list: {client.diffusion_list}")
            add_activity(request, "Client Edited : " + str(client.name))
            return redirect("clients")

        except Exception as e:
            print(f"DEBUG: Error in client_info edit: {e}")
            messages.error(request, f"Error updating client: {str(e)}")
            return render(
                request, "components/clients/client_info.html", {"client": client}
            )
    else:
        return render(
            request, "components/clients/client_info.html", {"client": client}
        )


@has_permission_required("w_clients")
def client_add(request):  # 2. Add a new Client
    if request.method == "POST":
        print(f"DEBUG: POST data keys: {list(request.POST.keys())}")
        print(f"DEBUG: POST data: {dict(request.POST)}")

        try:
            client_name = Validation.validate_name(request.POST.get("client_name"))
            client_email = Validation.validate_notRequired_email(
                request.POST.get("client_email")
            )
            client_phone_number = Validation.validate_notRequired_phoneNumber(
                request.POST.get("client_phone_number")
            )
            client_info = request.POST.get("client_info")

            # Handle diffusion list data
            diffusion_list = handle_diffusion_list(request)

            if request.FILES and "client_logo" in request.FILES:
                client_logo = Validation.validate_image(request.FILES["client_logo"])

                new_client = Client(
                    name=client_name,
                    email=client_email,
                    logo=client_logo,
                    phone_number=client_phone_number,
                    info=client_info,
                    diffusion_list=diffusion_list,
                )
            else:
                new_client = Client(
                    name=client_name,
                    email=client_email,
                    phone_number=client_phone_number,
                    info=client_info,
                    diffusion_list=diffusion_list,
                )

            new_client.save()
            print(
                f"DEBUG: Saved client with diffusion_list: {new_client.diffusion_list}"
            )
            add_activity(request, "Client Added : " + str(client_name))
            return redirect("clients")

        except Exception as e:
            print(f"DEBUG: Error in client_add: {e}")
            messages.error(request, f"Error creating client: {str(e)}")
            return render(request, "components/clients/client_add.html")

    else:
        return render(request, "components/clients/client_add.html")


@has_permission_required("w_clients")
def client_delete(request):  # 4. delete client
    client_id = request.POST.get("client_id")

    client = Validation.validate_object(Client, client_id)
    client_logo = client.logo
    if client_logo:
        client_logo.delete()

    add_activity(request, "Client Deleted : " + str(client.name))
    client.delete()
    return redirect("clients")


# ============================================== Templates ========================================
@has_permission_required("r_templates")
def templates(request):  # 1. View all Templates
    query = request.GET.get("q")
    if query:
        templates = Template.objects.filter(
            Q(name__icontains=query) | Q(about__icontains=query)
        )
    else:
        templates = Template.objects.all()

    paginator = Paginator(templates, 10)  # Show 10 clients per page
    templates_to_show = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "components/templates/templates_all.html",
        {"templates": templates_to_show},
    )


@has_permission_required("r_templates")
def template_info(request, template_id):  # 2. view/edit Templates
    template = Template.objects.get(id=template_id)
    if request.method == "GET":
        return render(
            request,
            "components/templates/templates_info.html",
            {
                "template": template,
                "charts_settings": json.dumps(template.chart_settings),
            },
        )

    elif request.method == "POST":
        user_permissions = request.user.userprofile.role.permissions.values_list(
            "name", flat=True
        )
        if "w_templates" not in user_permissions:
            raise PermissionDenied

        template.name = Validation.validate_name(request.POST.get("t_name"))
        template.about = request.POST.get("t_about")
        template.chart_settings = json.loads(
            Validation.validate_json(request.POST.get("t_chart_settings"))
        )

        if "t_file" in request.FILES:
            validated_temp = Validation.validate_notRequired_docxFile(
                request.FILES["t_file"]
            )
            if template.file:
                template.file.delete()
            template.file = validated_temp

        template.save()
        add_activity(request, "Template Edited : " + str(template.name))
        return redirect("templates")

    else:
        raise PermissionDenied


@has_permission_required("w_templates")
def template_add(request):  # 3. Add a new Templates
    if request.method == "GET":
        chart_default_setings = """{"charts": [{"type": "pie","title": "Vulnerability Risk Distribution (Pie)","x_label": "","y_label": "","size": 120,"colors": {"Critical": "#c00000","High": "#ff0000","Medium": "#ffc000","Low": "#ffff00"}},{"type": "bar","title": "Vulnerability Risk Distribution (Bar)","x_label": "Risk Levels","y_label": "Count","size": 120,"colors": {"Critical": "#c00000","High": "#ff0000","Medium": "#ffc000","Low": "#ffff00"}}]}"""
        return render(
            request,
            "components/templates/templates_add.html",
            {"chart_default_setings": chart_default_setings},
        )
    elif request.method == "POST":
        template_name = Validation.validate_name(request.POST.get("t_name"))
        template_about = request.POST.get("t_about")
        chart_settings = Validation.validate_json(request.POST.get("t_chart_settings"))

        if "t_file" in request.FILES:
            template_file = Validation.validate_docxFile(request.FILES["t_file"])

            new_template = Template(
                name=template_name,
                about=template_about,
                file=template_file,
                chart_settings=json.loads(chart_settings),
            )
            new_template.save()
        add_activity(request, "Template Added : " + str(template_name))
        return redirect("templates")

    else:
        return redirect("templates")


@has_permission_required("w_templates")
def template_delete(request):  # 4. delete template
    template_id = request.POST.get("template_id")
    template = Validation.validate_object(Template, template_id)
    file = template.file
    if file:
        file.delete()
    template.delete()

    add_activity(request, "Template Deleted : " + str(template.name))
    return redirect("templates")


@has_permission_required("r_templates")
def template_download(request, template_id):  # 5. download template
    template = get_object_or_404(Template, pk=template_id)
    # file_path = template.file.path
    # file_name = template.file.name.split('/')[-1]
    # file = File(open(file_path, 'rb'))
    # response = FileResponse(FileWrapper(file))
    # response['Content-Disposition'] = 'attachment; filename="{}"'.format(file_name)
    # return response
    return redirect(template.file.url)


# ============================================== Vulnerabilities ========================================
@has_permission_required("r_vulnerabilities")
def vulnerabilities(request):  # 1. View all vulns
    query = request.GET.get("q")
    if query:
        vulnerabilities = Vulnerability.objects.filter(
            Q(name__icontains=query)
            | Q(risk_rating__icontains=query)
            | Q(tag__icontains=query)
        )
    else:
        vulnerabilities = Vulnerability.objects.all()

    paginator = Paginator(vulnerabilities, 10)  # Show 10 clients per page
    vuln_to_show = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "components/vulnerabilities/vulnerabilities_all.html",
        {"vulnerabilities": vuln_to_show, "query": query},
    )


@has_permission_required("r_vulnerabilities")
def vulnerability_info(request, vulnerability_id):  # 3. view/edit vuln
    vulnerability = Vulnerability.objects.get(id=vulnerability_id)

    if request.method == "POST":
        user_permissions = request.user.userprofile.role.permissions.values_list(
            "name", flat=True
        )
        if "w_vulnerabilities" not in user_permissions:
            raise PermissionDenied
        if request.POST.get("v_name"):
            vulnerability.name = Validation.validate_name(request.POST.get("v_name"))
            vulnerability.cvss = (
                Validation.validate_cvss(request.POST.get("v_cvss")) or 0
            )
            vulnerability.risk_rating = Validation.validate_risk_rating(
                request.POST.get("v_risk_rating")
            )
            vulnerability.tag = request.POST.get("v_tag")
            vulnerability.description = request.POST.get("v_description")
            vulnerability.v_impact = request.POST.get("v_impact")
            vulnerability.remediation = request.POST.get("v_remediation")
            vulnerability.save()

            add_activity(request, "Vulnerability Edited : " + str(vulnerability.name))
            return redirect("vulnerabilities")

        elif request.POST.get("custom_key"):
            custom_key = request.POST.get("custom_key")
            custom_value = request.POST.get("custom_value")

            custom_fields = vulnerability.custom_fields or {}
            custom_fields[custom_key] = custom_value

            vulnerability.custom_fields = custom_fields
            vulnerability.save()

            event = "Vulnerability Edited : " + str(vulnerability.name)
            add_activity(request, event)
            return redirect("vulnerability_info", vulnerability_id=vulnerability_id)

    else:
        return render(
            request,
            "components/vulnerabilities/vulnerabilities_info.html",
            {"vulnerability": vulnerability},
        )


@has_permission_required("w_vulnerabilities")
def vulnerability_add(request):  # 2. Add a new vuln
    if request.method == "POST":
        vulnerability_name = Validation.validate_name(request.POST.get("v_name"))
        vulnerability_tag = request.POST.get("v_tag")
        vulnerability_cvss = Validation.validate_cvss(request.POST.get("v_cvss")) or 0
        vulnerability_risk_rating = Validation.validate_risk_rating(
            request.POST.get("v_risk_rating")
        )
        vulnerability_description = request.POST.get("v_description")
        vulnerability_impact = request.POST.get("v_impact")
        vulnerability_remediation = request.POST.get("v_remediation")
        new_vulnerability = Vulnerability(
            name=vulnerability_name,
            tag=vulnerability_tag,
            risk_rating=vulnerability_risk_rating,
            cvss=vulnerability_cvss,
            description=vulnerability_description,
            impact=vulnerability_impact,
            remediation=vulnerability_remediation,
        )
        new_vulnerability.save()

        if request.POST.get("custom_key"):
            custom_key = request.POST.get("custom_key")
            custom_value = request.POST.get("custom_value")

            custom_fields = new_vulnerability.custom_fields or {}
            custom_fields[custom_key] = custom_value

            new_vulnerability.custom_fields = custom_fields
            new_vulnerability.save()

            add_activity(
                request, "Vulnerability Added : " + str(new_vulnerability.name)
            )
            return redirect("vulnerability_info", vulnerability_id=new_vulnerability.id)

        add_activity(request, "Vulnerability Added : " + str(new_vulnerability.name))
        return redirect("vulnerabilities")

    else:
        return render(request, "components/vulnerabilities/vulnerability_add.html")


@has_permission_required("w_vulnerabilities")
def vulnerability_delete(request):  # 4. delete vuln
    vulnerability_id = request.POST.get("vulnerability_id")

    vulnerability = Validation.validate_object(Vulnerability, vulnerability_id)
    add_activity(request, "Vulnerability Deleted : " + str(vulnerability.name))

    vulnerability.delete()
    return redirect("vulnerabilities")


@has_permission_required("r_clients")
def debug_diffusion(request, client_id):
    """Debug view to check diffusion list data rendering"""
    try:
        client = Client.objects.get(id=client_id)
        return HttpResponse(
            f"""
        <html>
        <head><title>Debug Diffusion List</title></head>
        <body>
            <h1>Debug Info for Client: {client.name}</h1>
            <h2>Raw diffusion_list data:</h2>
            <pre>{client.diffusion_list}</pre>
            <h2>Type:</h2>
            <pre>{type(client.diffusion_list)}</pre>
            <h2>Length:</h2>
            <pre>{len(client.diffusion_list) if client.diffusion_list else 'None'}</pre>
            <h2>JSON escaped:</h2>
            <pre>'{json.dumps(client.diffusion_list) if client.diffusion_list else 'null'}'</pre>
            <script>
                console.log('Raw data:', {json.dumps(client.diffusion_list) if client.diffusion_list else 'null'});
                const data = {json.dumps(client.diffusion_list) if client.diffusion_list else 'null'};
                console.log('Parsed data:', data);
                console.log('Is array:', Array.isArray(data));
                if (Array.isArray(data)) {{
                    console.log('Array length:', data.length);
                    data.forEach((item, i) => console.log(`Item ${{i+1}}:`, item));
                }}
            </script>
        </body>
        </html>
        """
        )
    except Client.DoesNotExist:
        return HttpResponse("Client not found")


def handle_diffusion_list(request):
    """Helper function to process diffusion list data from request."""
    diffusion_list_data = request.POST.get("diffusion_list_data")
    print(f"DEBUG: Received diffusion_list_data: {diffusion_list_data}")

    if diffusion_list_data:
        try:
            import json

            diffusion_list = json.loads(diffusion_list_data)
            print(f"DEBUG: Parsed diffusion_list from JSON: {diffusion_list}")
            return diffusion_list
        except json.JSONDecodeError as e:
            print(f"DEBUG: JSON decode error: {e}")

    # Fallback: collect from individual form fields
    print("DEBUG: Attempting to collect diffusion data from individual fields")
    diffusion_list = []
    diffusion_counter = 1
    while True:
        name_key = f"diffusion_name_{diffusion_counter}"
        title_key = f"diffusion_title_{diffusion_counter}"
        email_key = f"diffusion_email_{diffusion_counter}"

        if name_key not in request.POST:
            break

        name = request.POST.get(name_key, "").strip()
        title = request.POST.get(title_key, "").strip()
        email = request.POST.get(email_key, "").strip()

        if name:  # Only add if name is provided
            contact_data = {"name": name, "title": title, "email": email}
            diffusion_list.append(contact_data)
            print(f"DEBUG: Added contact from individual fields: {contact_data}")

        diffusion_counter += 1

    print(f"DEBUG: Final diffusion_list from individual fields: {diffusion_list}")
    return diffusion_list
