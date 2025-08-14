from .models import (
    Assessment,
    AssessmentStatus,
    AssessmentFile,
    AssessmentVulnerability,
    TaskStatus,
)
from Threat_Track.custom_functions import render_short_codes, update_image_metadata
from django.http import FileResponse, HttpResponseRedirect, JsonResponse
from extras.reporting.reporting import genrate_report, all_in_one
from azure.storage.blob import BlobServiceClient, ContentSettings
from django.shortcuts import render, get_object_or_404, redirect
from .models import ChatMessage, AssessmentTask, CKImageUpload
from components.models import Client, Template, Vulnerability
from assessment_structures.models import Assessment_Structure
from Threat_Track.decorators import has_permission_required
from django.core.files.storage import default_storage
from django.core.exceptions import PermissionDenied
from Threat_Track.validations import Validation
from django.core.exceptions import BadRequest
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from activities.views import add_activity
from wsgiref.util import FileWrapper
from django.contrib import messages
from django.core.files import File
from django.conf import settings
from django.urls import reverse
from django.db.models import Q
from users.models import Team
from datetime import datetime
import os, csv, json, boto3


# Manipulate Assessments
@has_permission_required("view_assigned_assessments", "view_all_assessments")
def assessments(request):
    query = request.GET.get("q")
    selected_client = request.GET.get("client")
    selected_user = request.GET.get("selected_user")
    selected_status = request.GET.get("status")

    user_permissions = request.user.userprofile.role.permissions.values_list(
        "name", flat=True
    )
    if "view_all_assessments" in user_permissions:
        assessments_list = Assessment.objects.all().order_by("-start_date")
        assessments_list2 = Assessment.objects.all().order_by("-start_date")
    elif "view_assigned_assessments" in user_permissions:
        assessments_list = Assessment.objects.filter(
            assigned_users=request.user
        ).order_by("-start_date")
        assessments_list2 = Assessment.objects.filter(
            assigned_users=request.user
        ).order_by("-start_date")

    if not selected_client:
        selected_client = "0"

    if selected_client != "0":
        assessments_list = assessments_list.filter(client__id=selected_client)

    if selected_user:
        assessments_list = assessments_list.filter(
            assigned_users__username=selected_user
        )

    if selected_status:
        assessments_list = assessments_list.filter(status__name=selected_status)

    if query:
        assessments_list = assessments_list.filter(
            Q(name__icontains=query) | Q(client__name__icontains=query)
        ).order_by("-start_date")

    paginator = Paginator(assessments_list, 10)
    assessments = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "assessments/assessments_all.html",
        {
            "assessments": assessments,
            "clients": Client.objects.filter(
                assessments__in=assessments_list2
            ).distinct(),
            "users": User.objects.filter(
                assigned_assessments__in=assessments_list2
            ).distinct(),
            "assessmentstatuses": AssessmentStatus.objects.all(),
            "selected_client": int(selected_client),
            "selected_user": selected_user,
            "selected_status": selected_status,
            "query": query,
        },
    )


@has_permission_required("add_assessments")
def assessment_add(request):
    if request.method == "POST":
        name = Validation.validate_name(request.POST["name"])
        client = Validation.validate_object(Client, request.POST["client"])
        status = Validation.validate_object(AssessmentStatus, request.POST["status_id"])
        start_date = Validation.validate_date(request.POST["start_date"])
        end_date = Validation.validate_date(request.POST["end_date"])

        # Make sure start date is before end date
        if datetime.strptime(start_date, "%Y-%m-%d") > datetime.strptime(
            end_date, "%Y-%m-%d"
        ):
            raise BadRequest("Start Date must be before the end date")

        assessment = Assessment.objects.create(
            name=name,
            client=client,
            status=status,
            start_date=start_date,
            end_date=end_date,
            who_created=request.user,
        )
        (
            assessment.assigned_users.set(
                Validation.validate_users(request.POST.getlist("assigned_users"))
            )
            if request.POST.getlist("assigned_users")
            else None
        )

        if request.POST["assessment_structure_id"] != "0":
            assessment_structure = Validation.validate_object(
                Assessment_Structure, request.POST["assessment_structure_id"]
            )
            assessment.assessment_structure = (
                assessment_structure  # to link assessment structure with assessment
            )
            assessment.af_name = assessment_structure.name
            assessment.s_fields = assessment_structure.s_fields
            assessment.a_fields = assessment_structure.a_fields
            assessment.v_fields = assessment_structure.v_fields

            # auto assign if there's only 1 templaet
            if assessment_structure.template_file:
                pass

        assessment.save()

        # messages.success(request, "Assessment created")
        add_activity(request, "Assessment created: " + str(name))
        return HttpResponseRedirect(reverse("assessments"))

    else:
        clients = Client.objects.all()
        assessment_structures = Assessment_Structure.objects.all()
        statuses = AssessmentStatus.objects.all()
        teams = Team.objects.all()
        users = User.objects.all()

        return render(
            request,
            "assessments/assessment_add.html",
            {
                "clients": clients,
                "assessment_structures": assessment_structures,
                "statuses": statuses,
                "teams": teams,
                "users": users,
            },
        )


@has_permission_required("edit_assessments")
def assessment_edit(request, assessment_id):
    assessment = Validation.validate_object(Assessment, assessment_id)
    user_permissions = request.user.userprofile.role.permissions.values_list(
        "name", flat=True
    )
    if (
        request.user in assessment.assigned_users.all()
        or "view_all_assessments" in user_permissions
    ):
        if request.method == "POST":
            assessment.name = Validation.validate_name(request.POST["name"])
            assessment.status = Validation.validate_object(
                AssessmentStatus, request.POST["status_id"]
            )
            assessment.client = Validation.validate_object(
                Client, request.POST["client"]
            )
            assessment.assigned_users.set(
                Validation.validate_users(request.POST.getlist("assigned_users"))
            )

            assessment.start_date = Validation.validate_date(request.POST["start_date"])
            assessment.end_date = Validation.validate_date(request.POST["end_date"])

            if datetime.strptime(
                request.POST["start_date"], "%Y-%m-%d"
            ) > datetime.strptime(request.POST["end_date"], "%Y-%m-%d"):
                raise BadRequest("Start Date must be before the end date")

            if (
                request.POST["assessment_structure_id"] != "0"
            ):  # Changing the assessment struckture
                assessment_structure = Validation.validate_object(
                    Assessment_Structure, request.POST["assessment_structure_id"]
                )
                if (
                    assessment_structure.name != assessment.af_name
                ):  # cheak if the assessment struckture is changed
                    assessment.assessment_structure = assessment_structure
                    assessment.af_name = assessment_structure.name
                    assessment.s_fields = assessment_structure.s_fields
                    assessment.a_fields = assessment_structure.a_fields
                    assessment.v_fields = assessment_structure.v_fields

                    if assessment_structure.template_file:
                        pass

                    for vulnerability in assessment.vulnerabilities.all():
                        vulnerability.fields = assessment_structure.v_fields
                        vulnerability.save()

            elif (
                request.POST["assessment_structure_id"] == "0"
            ):  # No assessment struckture
                assessment.assessment_structure = None
                assessment.af_name = None
                assessment.s_fields = None
                assessment.a_fields = None
                assessment.v_fields = None

            assessment.save()
            add_activity(request, "Assessment edited: " + str(assessment))
            return HttpResponseRedirect(
                reverse("assessment_summary", args=[assessment_id])
            )

        else:
            clients = Client.objects.all()
            assessment_structures = Assessment_Structure.objects.all()
            statuses = AssessmentStatus.objects.all()
            teams = Team.objects.all()
            users = User.objects.all()
            return render(
                request,
                "assessments/assessment_edit.html",
                {
                    "assessment": assessment,
                    "clients": clients,
                    "assessment_structures": assessment_structures,
                    "statuses": statuses,
                    "teams": teams,
                    "users": users,
                },
            )
    else:
        raise PermissionDenied


@has_permission_required("delete_assessments")
def assessment_delete(request):
    user_permissions = request.user.userprofile.role.permissions.values_list(
        "name", flat=True
    )
    assessment_id = request.POST.get("id")
    assessment = Validation.validate_object(Assessment, assessment_id)
    if (
        request.user in assessment.assigned_users.all()
        or "view_all_assessments" in user_permissions
    ):

        # 1. Delete all CK images in this Assessment (Addtional fileds)
        matching_ck_img_objects = CKImageUpload.objects.filter(
            for_model="Assessment", model_id=assessment_id
        )
        for img in matching_ck_img_objects:
            img.image.delete()
            img.delete()

        # 2. Delete all vulnerabilities in this assessment & all the CK images for this vulnerability
        for vuln in assessment.vulnerabilities.all():
            matching_ck_img_objects = CKImageUpload.objects.filter(
                for_model="AssessmentVulnerability", model_id=vuln.id
            )
            for img in matching_ck_img_objects:
                img.image.delete()
                img.delete()

            vuln.delete()

        # 3. Delete all attached files in this assessment
        for file in assessment.files.all():
            if file.file:
                file.file.delete()
            file.delete()

        # 4. Delete all the realted tasks
        for task in assessment.tasks.all():
            task.delete()

        # 5. Delete The Assessment itself
        assessment.delete()
        add_activity(request, "Assessment delete: " + str(assessment))
        return redirect("assessments")
    else:
        raise PermissionDenied


@has_permission_required("r_assessment_summary")
def assessment_summary(request, assessment_id):
    assessment = Validation.validate_object(Assessment, assessment_id)
    user_permissions = request.user.userprofile.role.permissions.values_list(
        "name", flat=True
    )
    if (
        request.user in assessment.assigned_users.all()
        or "view_all_assessments" in user_permissions
    ):
        return render(
            request, "assessments/assessment_summary.html", {"assessment": assessment}
        )
    else:
        raise PermissionDenied


@has_permission_required("r_assessment_additional_fields")
def assessment_additional_fields(request, assessment_id):
    assessment = Validation.validate_object(Assessment, assessment_id)
    user_permissions = request.user.userprofile.role.permissions.values_list(
        "name", flat=True
    )
    if (
        request.user in assessment.assigned_users.all()
        or "view_all_assessments" in user_permissions
    ):
        return render(
            request,
            "assessments/assessment_additional_fields.html",
            {"assessment": assessment, "fields": Assessment_Structure.objects.all()},
        )
    else:
        raise PermissionDenied


@has_permission_required("r_assessment_vulnerabilities")
def assessment_vulnerabilities(request, assessment_id):
    assessment = Validation.validate_object(Assessment, assessment_id)
    user_permissions = request.user.userprofile.role.permissions.values_list(
        "name", flat=True
    )
    if (
        request.user in assessment.assigned_users.all()
        or "view_all_assessments" in user_permissions
    ):
        selected_risk = request.GET.get("selected_risk")
        selected_status = request.GET.get("selected_status")
        query = request.GET.get("q")

        total_vulnerabilities = assessment.vulnerabilities.all()
        vulnerabilities_list = assessment.vulnerabilities.all().order_by("number")

        if selected_risk:
            vulnerabilities_list = vulnerabilities_list.filter(
                risk_rating=selected_risk
            )

        if selected_status:
            vulnerabilities_list = vulnerabilities_list.filter(status=selected_status)

        if query:
            vulnerabilities_list = vulnerabilities_list.filter(
                Q(name__icontains=query)
                | Q(number__icontains=query)
                | Q(target__icontains=query)
                | Q(tag__icontains=query)
                | Q(cvss__icontains=query)
                | Q(risk_rating__icontains=query)
            ).order_by("number")

        context = {
            "assessment": assessment,
            "vulnerabilities": vulnerabilities_list,
            "selected_risk": selected_risk,
            "selected_status": selected_status,
            "total_vulnerabilities": len(total_vulnerabilities),
            "vulnerabilities_list": len(vulnerabilities_list),
        }

        if len(vulnerabilities_list) > 0:  # to display progress bar
            total_c_risk = len(vulnerabilities_list.filter(risk_rating="Critical"))
            total_h_risk = len(vulnerabilities_list.filter(risk_rating="High"))
            total_m_risk = len(vulnerabilities_list.filter(risk_rating="Medium"))
            total_l_risk = len(vulnerabilities_list.filter(risk_rating="Low"))

            percent_c_risk = total_c_risk / len(vulnerabilities_list) * 100
            percent_h_risk = total_h_risk / len(vulnerabilities_list) * 100
            percent_m_risk = total_m_risk / len(vulnerabilities_list) * 100
            percent_l_risk = total_l_risk / len(vulnerabilities_list) * 100

            context = {
                "assessment": assessment,
                "vulnerabilities": vulnerabilities_list,
                "selected_risk": selected_risk,
                "selected_status": selected_status,
                "vulnerabilities_list": len(vulnerabilities_list),
                "total_vulnerabilities": len(total_vulnerabilities),
                "total_c_risk": total_c_risk,
                "total_h_risk": total_h_risk,
                "total_m_risk": total_m_risk,
                "total_l_risk": total_l_risk,
                "percent_c_risk": percent_c_risk,
                "percent_h_risk": percent_h_risk,
                "percent_m_risk": percent_m_risk,
                "percent_l_risk": percent_l_risk,
            }

        return render(request, "assessments/assessment_vulnerabilities.html", context)
    else:
        raise PermissionDenied


@has_permission_required("r_assessment_attached_files")
def assessment_attached_files(request, assessment_id):
    assessment = Validation.validate_object(Assessment, assessment_id)

    user_permissions = request.user.userprofile.role.permissions.values_list(
        "name", flat=True
    )
    if (
        request.user in assessment.assigned_users.all()
        or "view_all_assessments" in user_permissions
    ):
        if request.method == "GET":
            return render(
                request,
                "assessments/assessment_attached_files.html",
                {"assessment": assessment},
            )

        elif request.method == "POST":
            if "w_assessment_attached_files" not in user_permissions:
                raise PermissionDenied
            else:
                file = request.FILES.get("file")
                if file:
                    if file.size > 20 * 1024 * 1024:
                        messages.error(
                            request, "File size exceeds the allowed limit of 20MB"
                        )
                        return redirect(
                            "assessment_attached_files", assessment_id=assessment.id
                        )

                    new_file = AssessmentFile(
                        name=file.name, file=file, added_by=request.user
                    )
                    new_file.save()

                    # Update metadata of files in S3 or Blob
                    (
                        update_image_metadata(new_file.file.name)
                        if settings.MEDIA_STORAGE_TYPE in ["S3", "BLOB"]
                        else None
                    )

                    assessment.files.add(new_file)
                    assessment.save()

                return redirect(
                    "assessment_attached_files", assessment_id=assessment_id
                )
    else:
        raise PermissionDenied


@has_permission_required("r_assessment_tasks")
def assessment_tasks(request, assessment_id):
    assessment = Validation.validate_object(Assessment, assessment_id)
    user_permissions = request.user.userprofile.role.permissions.values_list(
        "name", flat=True
    )
    if (
        request.user in assessment.assigned_users.all()
        or "view_all_assessments" in user_permissions
    ):
        tasks_to_load = assessment.tasks.all().order_by("-id")
        statuss_to_load = TaskStatus.objects.all()
        users = assessment.assigned_users.all()
        return render(
            request,
            "assessments/assessment_tasks.html",
            {
                "assessment": assessment,
                "tasks_to_load": tasks_to_load,
                "statuss_to_load": statuss_to_load,
                "users": users,
            },
        )
    else:
        raise PermissionDenied


@has_permission_required("r_assessment_chat_room")
def assessment_chat_room(request, assessment_id):
    assessment = get_object_or_404(Assessment, pk=assessment_id)

    user_permissions = request.user.userprofile.role.permissions.values_list(
        "name", flat=True
    )
    if (
        request.user in assessment.assigned_users.all()
        or "view_all_assessments" in user_permissions
    ):

        if request.method == "POST":
            if "w_assessment_chat_room" not in user_permissions:
                raise PermissionDenied
            else:
                if request.POST.get("message"):
                    new_message = ChatMessage(
                        assessment=assessment,
                        sender=request.user,
                        message=request.POST.get("message"),
                    )
                    new_message.save()
                return redirect("assessment_chat_room", assessment_id=assessment_id)

        elif request.method == "GET":
            messages_to_view = ChatMessage.objects.filter(assessment=assessment)
            return render(
                request,
                "assessments/assessment_chat_room.html",
                {"assessment": assessment, "messages_to_view": messages_to_view},
            )
    else:
        raise PermissionDenied


@has_permission_required("generate_report")
def assessment_reporting(request, assessment_id):
    assessment = Validation.validate_object(Assessment, assessment_id)
    assessment_dict = all_in_one(assessment)
    user_permissions = request.user.userprofile.role.permissions.values_list(
        "name", flat=True
    )

    if (
        request.user in assessment.assigned_users.all()
        or "view_all_assessments" in user_permissions
    ):
        if request.method == "POST":
            if request.POST.get("template_from_structure"):
                # use template from assessment structure
                assessment_structure_id = request.POST.get("template_from_structure")
                assessment_structure = Validation.validate_object(
                    Assessment_Structure, assessment_structure_id
                )

                if not assessment_structure.template_file:
                    messages.error(
                        request,
                        "Selected assessment structure does not have a template file",
                    )
                    return redirect("assessment_reporting", assessment_id=assessment.id)

                temp_template = Template(
                    name=assessment_structure.template_name
                    or "Assessment Structure Template",
                    file=assessment_structure.template_file,
                    chart_settings=assessment_structure.chart_settings or {},
                )

                try:
                    genrated_report = genrate_report(temp_template, assessment_dict)
                except Exception as error:
                    messages.error(request, str(error))
                    return redirect("assessment_reporting", assessment_id=assessment.id)

                return genrated_report

            elif request.POST.get("template_from_comp"):
                template_obj = Validation.validate_object(
                    Template, request.POST.get("template_from_comp")
                )

                try:
                    genrated_report = genrate_report(template_obj, assessment_dict)
                except Exception as error:
                    messages.error(request, str(error))
                    return redirect("assessment_reporting", assessment_id=assessment.id)

                return genrated_report

            elif request.FILES.get("template_from_upload"):
                uploaded_file = Validation.validate_docxFile(
                    request.FILES["template_from_upload"]
                )

                new_template_object = Template(
                    name="tmp",
                    file=uploaded_file,
                    chart_settings=json.loads(
                        """{"charts": [{"type": "pie","title": "Vulnerability Risk Distribution (Pie)","x_label": "","y_label": "","size": 120,"colors": {"Critical": "#c00000","High": "#ff0000","Medium": "#ffc000","Low": "#ffff00"}},{"type": "bar","title": "Vulnerability Risk Distribution (Bar)","x_label": "Risk Levels","y_label": "Count","size": 120,"colors": {"Critical": "#c00000","High": "#ff0000","Medium": "#ffc000","Low": "#ffff00"}}]} """
                    ),
                )

                try:
                    genrated_report = genrate_report(
                        new_template_object, assessment_dict
                    )
                    new_template_object.file.delete()
                    new_template_object.delete()
                except Exception as error:
                    new_template_object.file.delete()
                    new_template_object.delete()
                    messages.error(request, str(error))
                    return redirect("assessment_reporting", assessment_id=assessment.id)

                return genrated_report

            else:
                raise BadRequest("Did not choose/upload a template")

        else:
            assessment_structures_with_templates = Assessment_Structure.objects.exclude(
                template_file__isnull=True
            ).exclude(template_file__exact="")

            if (
                assessment.assessment_structure
                and assessment.assessment_structure.template_file
            ):
                assessment_structures_with_templates = (
                    assessment_structures_with_templates.union(
                        Assessment_Structure.objects.filter(
                            id=assessment.assessment_structure.id
                        )
                    )
                )

            return render(
                request,
                "assessments/assessment_reporting.html",
                {
                    "assessment": assessment,
                    "assessment_dict": assessment_dict,
                    "templates": Template.objects.all(),
                    "assessment_structures_with_templates": assessment_structures_with_templates,
                },
            )

    else:
        raise PermissionDenied


@has_permission_required("w_assessment_vulnerabilities")
def assessment_vulnerabilities_add(request, assessment_id):
    assessment = Validation.validate_object(Assessment, assessment_id)
    user_permissions = request.user.userprofile.role.permissions.values_list(
        "name", flat=True
    )
    if (
        request.user in assessment.assigned_users.all()
        or "view_all_assessments" in user_permissions
    ):
        if request.method == "POST":
            v_fileds = assessment.v_fields
            new_vulnerability = AssessmentVulnerability(
                assessment=assessment,
                name=Validation.validate_name(request.POST.get("v_name")),
                status=Validation.validate_vuln_status(
                    request.POST.get("v_status")
                ),  # TODO make sure it is on of 2
                cvss=Validation.validate_cvss(request.POST.get("v_cvss")) or 0,
                risk_rating=Validation.validate_risk_rating(
                    request.POST.get("v_risk_rating")
                ),
                tag=request.POST.get("v_tag"),
                target=request.POST.get("v_target"),
                description=request.POST.get("v_description"),
                impact=request.POST.get("v_impact"),
                remediation=request.POST.get("v_remediation"),
                poc_text=request.POST.get("v_poc_text"),
                fields=v_fileds,
            )

            if new_vulnerability.fields:
                for v_filed in new_vulnerability.fields:
                    if request.POST.get(v_filed):
                        new_vulnerability.fields[v_filed] = request.POST.get(v_filed)

            new_vulnerability.save()
            assessment.vulnerabilities.add(new_vulnerability)

            # Set new ck image objects to this AssessmentVulnerability
            matching_ck_img_objects = CKImageUpload.objects.filter(
                for_model="AssessmentVulnerability", model_id=0
            )
            for img in matching_ck_img_objects:
                img.model_id = new_vulnerability.id
                img.save()

            add_activity(
                request,
                "Vulnerability Added to assessment: " + str(new_vulnerability.name),
            )
            return redirect("assessment_vulnerabilities", assessment_id=assessment.id)

        elif request.method == "GET":
            if not request.GET.get("vuln_to_load_id"):
                return render(
                    request,
                    "assessments/assessment_vulnerabilities_add.html",
                    {"assessment": assessment, "com_vuln": Vulnerability.objects.all()},
                )

            else:
                vuln_to_load = get_object_or_404(
                    Vulnerability, pk=request.GET.get("vuln_to_load_id")
                )
                response_data = {
                    "vuln_tag": vuln_to_load.tag,
                    "vuln_name": vuln_to_load.name,
                    "vuln_cvss": vuln_to_load.cvss,
                    "vuln_risk_rating": vuln_to_load.risk_rating,
                    "vuln_description": vuln_to_load.description,
                    "vuln_impact": vuln_to_load.impact,
                    "vuln_remediation": vuln_to_load.remediation,
                }
                return JsonResponse(response_data)

    else:
        raise PermissionDenied


@has_permission_required("w_assessment_vulnerabilities")
def assessment_vulnerabilities_add_from_scan(request, assessment_id):
    assessment = Validation.validate_object(Assessment, assessment_id)
    user_permissions = request.user.userprofile.role.permissions.values_list(
        "name", flat=True
    )
    if (
        request.user in assessment.assigned_users.all()
        or "view_all_assessments" in user_permissions
    ):
        if request.method == "POST":
            scan_file = request.FILES.get("scan_file")
            scan_type = request.POST.get("scan_type")
            if scan_type == "nessuss":
                reader = csv.reader(scan_file.read().decode("utf-8").splitlines())
                next(reader)
                for row in reader:
                    if len(row) >= 10:
                        cve = row[1]
                        cvss_score = row[2]
                        risk = row[3]
                        host = row[4]
                        protocol = row[5]
                        port = row[6]
                        name = row[7]
                        description = row[9]
                        solution = row[10]

                        if cvss_score:
                            new_vulnerability = AssessmentVulnerability(
                                assessment=assessment,
                                status="Unresolved",
                                target=host
                                + ":"
                                + port
                                + " ("
                                + protocol.upper()
                                + ")",
                                name=name,
                                description=description,
                                tag=cve,
                                cvss=cvss_score or 0,
                                risk_rating=risk,
                                remediation=solution,
                                fields=assessment.v_fields,
                            )
                            new_vulnerability.save()
                            assessment.vulnerabilities.add(new_vulnerability)

                event = "Added Nessuss results to Assessment : " + str(assessment.name)
                add_activity(request, event)
                return redirect(
                    "assessment_vulnerabilities", assessment_id=assessment.id
                )

            elif scan_type == "openvas":
                return redirect(
                    "assessment_vulnerabilities", assessment_id=assessment.id
                )
        else:
            return redirect("assessments")
    else:
        return redirect("assessments")


@has_permission_required("r_assessment_vulnerabilities")
def assessment_vulnerability_edit(request, assessment_id, vulnerability_id):
    assessment = Validation.validate_object(Assessment, assessment_id)
    assessment_vulnerability = AssessmentVulnerability.objects.get(id=vulnerability_id)
    user_permissions = request.user.userprofile.role.permissions.values_list(
        "name", flat=True
    )
    if (
        request.user in assessment.assigned_users.all()
        or "view_all_assessments" in user_permissions
    ):
        if request.method == "GET":
            return render(
                request,
                "assessments/assessment_vulnerability_edit.html",
                {
                    "assessment": assessment,
                    "assessment_vulnerability": assessment_vulnerability,
                },
            )

        elif request.method == "POST":
            if "w_assessment_vulnerabilities" not in user_permissions:
                raise PermissionDenied

            assessment_vulnerability.name = Validation.validate_name(
                request.POST.get("v_name")
            )
            assessment_vulnerability.status = Validation.validate_vuln_status(
                request.POST.get("v_status")
            )
            assessment_vulnerability.cvss = (
                Validation.validate_cvss(request.POST.get("v_cvss"))
                if request.POST.get("v_cvss")
                else 0
            )
            assessment_vulnerability.risk_rating = Validation.validate_risk_rating(
                request.POST.get("v_risk_rating")
            )

            assessment_vulnerability.target = request.POST.get("v_target")
            assessment_vulnerability.tag = request.POST.get("v_tag")
            assessment_vulnerability.description = request.POST.get("v_description")
            assessment_vulnerability.impact = request.POST.get("v_impact")
            assessment_vulnerability.remediation = request.POST.get("v_remediation")
            assessment_vulnerability.poc_text = request.POST.get("v_poc_text")

            if assessment_vulnerability.fields:
                for v_filed in assessment_vulnerability.fields:
                    assessment_vulnerability.fields[v_filed] = request.POST.get(v_filed)
            assessment_vulnerability.save()

            if request.POST.get("edit") == "1":  # if the user clicked edit just edit
                add_activity(
                    request,
                    "Assessment Vulnerability Edited : "
                    + str(assessment_vulnerability.name)
                    + "at "
                    + str(assessment.name),
                )
                return redirect(
                    "assessment_vulnerabilities", assessment_id=assessment_id
                )

            elif (
                request.POST.get("render_short_codes") == "1"
            ):  # the user cicked on render short codes
                try:
                    assessment_dict = all_in_one(assessment)
                    assessment_vulnerability.name = Validation.validate_name(
                        render_short_codes(request.POST.get("v_name"), assessment_dict)
                    )
                    assessment_vulnerability.status = Validation.validate_vuln_status(
                        request.POST.get("v_status")
                    )
                    assessment_vulnerability.cvss = (
                        Validation.validate_cvss(request.POST.get("v_cvss"))
                        if request.POST.get("v_cvss")
                        else 0
                    )
                    assessment_vulnerability.risk_rating = (
                        Validation.validate_risk_rating(
                            request.POST.get("v_risk_rating")
                        )
                    )

                    assessment_vulnerability.target = render_short_codes(
                        request.POST.get("v_target"), assessment_dict
                    )
                    assessment_vulnerability.tag = render_short_codes(
                        request.POST.get("v_tag"), assessment_dict
                    )
                    assessment_vulnerability.description = render_short_codes(
                        request.POST.get("v_description"), assessment_dict
                    )
                    assessment_vulnerability.impact = render_short_codes(
                        request.POST.get("v_impact"), assessment_dict
                    )
                    assessment_vulnerability.remediation = render_short_codes(
                        request.POST.get("v_remediation"), assessment_dict
                    )
                    assessment_vulnerability.poc_text = render_short_codes(
                        request.POST.get("v_poc_text"), assessment_dict
                    )

                    if assessment_vulnerability.fields:
                        for v_filed in assessment_vulnerability.fields:
                            assessment_vulnerability.fields[v_filed] = (
                                render_short_codes(
                                    request.POST.get(v_filed), assessment_dict
                                )
                            )

                    assessment_vulnerability.save()
                    messages.success(request, "Shortcodes rendered successfully")
                    return redirect(
                        "assessment_vulnerability_edit",
                        assessment_id=assessment.id,
                        vulnerability_id=assessment_vulnerability.id,
                    )

                except Exception as error:
                    messages.error(request, str(error))
                return redirect(
                    "assessment_vulnerability_edit",
                    assessment_id=assessment.id,
                    vulnerability_id=assessment_vulnerability.id,
                )

    else:
        raise PermissionDenied


@has_permission_required("w_assessment_vulnerabilities")
def assessment_vulnerability_delete(request):
    assessment_id = request.POST.get("assessment_id")
    vulnerability_id = request.POST.get("vulnerability_id")

    assessment = get_object_or_404(Assessment, pk=assessment_id)
    user_permissions = request.user.userprofile.role.permissions.values_list(
        "name", flat=True
    )
    if (
        request.user in assessment.assigned_users.all()
        or "view_all_assessments" in user_permissions
    ):
        vulnerability = get_object_or_404(AssessmentVulnerability, pk=vulnerability_id)

        # delete related CK image objects
        matching_ck_img_objects = CKImageUpload.objects.filter(
            for_model="AssessmentVulnerability", model_id=vulnerability.id
        )
        for img in matching_ck_img_objects:
            img.image.delete()
            img.delete()

        vulnerability.delete()
        return redirect("assessment_vulnerabilities", assessment_id=assessment_id)
    else:
        raise PermissionDenied


@has_permission_required("r_assessment_attached_files")
def download_file(request, assessment_id, file_id):
    assessment = get_object_or_404(Assessment, pk=assessment_id)
    file = get_object_or_404(AssessmentFile, pk=file_id)
    user_permissions = request.user.userprofile.role.permissions.values_list(
        "name", flat=True
    )
    if (
        request.user in assessment.assigned_users.all()
        or "view_all_assessments" in user_permissions
    ):
        return HttpResponseRedirect(file.file.url)
    else:
        raise PermissionDenied


@has_permission_required("w_assessment_attached_files")
def delete_file(request):
    assessment_id = request.POST.get("assessment_id")
    file_id = request.POST.get("file_id")
    assessment = get_object_or_404(Assessment, pk=assessment_id)
    user_permissions = request.user.userprofile.role.permissions.values_list(
        "name", flat=True
    )
    if (
        request.user in assessment.assigned_users.all()
        or "view_all_assessments" in user_permissions
    ):
        file = get_object_or_404(AssessmentFile, pk=file_id)
        if file.file:
            file.file.delete()
        file.delete()
        return redirect("assessment_attached_files", assessment_id=assessment_id)
    else:
        raise PermissionDenied


@has_permission_required("w_assessment_tasks")
def add_task(request, assessment_id):
    assessment = get_object_or_404(Assessment, pk=assessment_id)
    user_permissions = request.user.userprofile.role.permissions.values_list(
        "name", flat=True
    )
    if (
        request.user in assessment.assigned_users.all()
        or "view_all_assessments" in user_permissions
    ):
        if request.method == "POST":
            task_name = request.POST["f_task"]
            status = Validation.validate_object(
                TaskStatus, int(request.POST["f_status"])
            )
            assigned_users = Validation.validate_users(
                request.POST.getlist("assigned_users")
            )
            task_to_add = AssessmentTask.objects.create(task=task_name, status=status)

            # only assign users who are part of the assessment
            assigned_users_objects = User.objects.filter(id__in=assigned_users)
            for user in assigned_users_objects:
                if user not in assessment.assigned_users.all():
                    raise BadRequest(
                        "You can only assign users who are part of the assessment"
                    )

            task_to_add.assigned_to.set(assigned_users)
            task_to_add.save()

            assessment.tasks.add(task_to_add)  # Add the task to the assessment
            assessment.save()
            messages.success(request, "Task added successfully")
            return redirect("assessment_tasks", assessment_id)

        elif request.method == "GET":
            statuss_to_load = TaskStatus.objects.all()
            assigned_users = assessment.assigned_users.all()
            return render(
                request,
                "assessments/assessment_task_add.html",
                {
                    "assessment": assessment,
                    "statuss_to_load": statuss_to_load,
                    "assigned_users": assigned_users,
                },
            )
    else:
        raise PermissionDenied


@has_permission_required("w_assessment_tasks")
def edit_task(request, assessment_id, task_id):
    assessment = get_object_or_404(Assessment, pk=assessment_id)
    user_permissions = request.user.userprofile.role.permissions.values_list(
        "name", flat=True
    )
    task = get_object_or_404(AssessmentTask, pk=task_id)

    if (
        request.user in assessment.assigned_users.all()
        or "view_all_assessments" in user_permissions
    ):
        if request.method == "POST":
            if "f_task" in request.POST:
                task.task = request.POST["f_task"]

            if "f_status" in request.POST:
                task.status = Validation.validate_object(
                    TaskStatus, int(request.POST["f_status"])
                )

            if "assigned_users" in request.POST:
                assigned_users = Validation.validate_users(
                    request.POST.getlist("assigned_users")
                )
                # only assign users who are part of the assessment
                assigned_users_objects = User.objects.filter(id__in=assigned_users)
                for user in assigned_users_objects:
                    if user not in assessment.assigned_users.all():
                        raise BadRequest(
                            "You can only assign users who are part of the assessment"
                        )
                task.assigned_to.set(assigned_users)

            task.save()
            messages.success(request, "Task edit successfully")
            return redirect("assessment_tasks", assessment_id)

        elif request.method == "GET":
            statuss_to_load = TaskStatus.objects.all()
            assigned_users = assessment.assigned_users.all()
            task_to_edit = task
            return render(
                request,
                "assessments/assessment_task_edit.html",
                {
                    "assessment": assessment,
                    "statuss_to_load": statuss_to_load,
                    "assigned_users": assigned_users,
                    "task_to_edit": task_to_edit,
                },
            )
    else:
        raise PermissionDenied


# Mainpulate Addtional Fileds for (Summary and af)
@has_permission_required("w_assessment_summary", "w_assessment_additional_fields")
def assessment_field_edit(request, assessment_id, f_for, key):
    assessment = Validation.validate_object(Assessment, assessment_id)
    user_permissions = request.user.userprofile.role.permissions.values_list(
        "name", flat=True
    )
    if (
        request.user in assessment.assigned_users.all()
        or "view_all_assessments" in user_permissions
    ):
        if request.method == "POST":

            if f_for == "s":
                if "w_assessment_summary" not in user_permissions:
                    raise PermissionDenied

                assessment.s_fields[key] = request.POST[key]
                assessment.save()
                return redirect("assessment_summary", assessment_id=assessment.id)

            if f_for == "a":
                if "w_assessment_additional_fields" not in user_permissions:
                    raise PermissionDenied
                assessment.a_fields[key] = request.POST[key]
                assessment.save()
                return redirect(
                    "assessment_additional_fields", assessment_id=assessment.id
                )

        elif request.method == "GET":
            return render(
                request,
                "assessments/assessment_additional_field_edit.html",
                {"assessment": assessment, "key_to_edit": key, "f_for": f_for},
            )

    else:
        raise PermissionDenied


@has_permission_required("w_assessment_summary", "w_assessment_additional_fields")
def assessment_field_delete(request):
    assessment_id = request.POST.get("id")
    f_for = request.POST.get("for")
    key = request.POST.get("key")

    assessment = Validation.validate_object(Assessment, assessment_id)
    user_permissions = request.user.userprofile.role.permissions.values_list(
        "name", flat=True
    )
    if (
        request.user in assessment.assigned_users.all()
        or "view_all_assessments" in user_permissions
    ):

        assessment = Assessment.objects.get(pk=assessment_id)

        if f_for == "s":
            if "w_assessment_summary" not in user_permissions:
                raise PermissionDenied
            if key in assessment.s_fields:
                del assessment.s_fields[key]
            assessment.save()
            messages.success(request, "Additional field deleted: " + str(key))
            return redirect("assessment_summary", assessment_id=assessment.id)

        elif f_for == "a":
            if "w_assessment_additional_fields" not in user_permissions:
                raise PermissionDenied
            if key in assessment.a_fields:
                del assessment.a_fields[key]
            assessment.save()
            messages.success(request, "Additional field deleted: " + str(key))
            return redirect("assessment_additional_fields", assessment_id=assessment.id)

        else:
            raise BadRequest
    else:
        raise PermissionDenied


@has_permission_required("w_assessment_summary", "w_assessment_additional_fields")
def assessment_field_render_shortcodes_key(request, assessment_id, f_for, key):
    assessment = Validation.validate_object(Assessment, assessment_id)
    assessment_dict = all_in_one(assessment)

    user_permissions = request.user.userprofile.role.permissions.values_list(
        "name", flat=True
    )
    if (
        request.user in assessment.assigned_users.all()
        or "view_all_assessments" in user_permissions
    ):
        if request.method == "GET":
            assessment = Assessment.objects.get(pk=assessment_id)
            try:
                if f_for == "s":
                    if "w_assessment_summary" not in user_permissions:
                        raise PermissionDenied
                    if key in assessment.s_fields:
                        assessment.s_fields[key] = render_short_codes(
                            assessment.s_fields[key], assessment_dict
                        )
                    assessment.save()
                    messages.success(
                        request, "Shortcodes rendered successfully for " + str(key)
                    )
                    return redirect("assessment_summary", assessment_id=assessment.id)

                elif f_for == "a":
                    if "w_assessment_additional_fields" not in user_permissions:
                        raise PermissionDenied
                    if key in assessment.a_fields:
                        assessment.a_fields[key] = render_short_codes(
                            assessment.a_fields[key], assessment_dict
                        )
                    assessment.save()
                    messages.success(
                        request, "Shortcodes rendered successfully for " + str(key)
                    )
                    return redirect(
                        "assessment_additional_fields", assessment_id=assessment.id
                    )

                else:
                    raise BadRequest("")

            except Exception as error:
                messages.error(request, str(error) + " - At " + str(key))
                return redirect("assessment_summary", assessment_id=assessment.id)
    else:
        raise PermissionDenied
