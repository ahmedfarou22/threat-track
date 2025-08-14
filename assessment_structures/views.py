from django.shortcuts import render, redirect
from activities.views import add_activity
from assessments.models import CKImageUpload
from Threat_Track.decorators import has_permission_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib import messages
from django.core.exceptions import BadRequest
from .models import Assessment_Structure
from Threat_Track.validations import Validation
import json

# Create your views here.


# ==============================================  Assessment Structures ========================================
@has_permission_required("r_assessment_structure")
def assessment_structures(request):  # 1. Assessment Structures all
    query = request.GET.get("q")
    if query:
        assessment_structures = Assessment_Structure.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    else:
        assessment_structures = Assessment_Structure.objects.all()

    paginator = Paginator(assessment_structures, 10)  # Show 10 clients per page
    assessment_structures_to_show = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "assessment_structures/assessment_structures_all.html",
        {"assessment_structures_to_show": assessment_structures_to_show},
    )


@has_permission_required("w_assessment_structure")
def assessment_structure_add(request):  # 2. Add a new  Assessment Structure
    if request.method == "POST":
        assessment_structure_name = Validation.validate_name(
            request.POST.get("as_name")
        )
        assessment_structure_description = request.POST.get("as_description")

        new_as = Assessment_Structure(
            name=assessment_structure_name, description=assessment_structure_description
        )
        new_as.save()

        event = "New Assessment Structure Added : " + str(new_as.name)
        add_activity(request, event)
        return redirect("assessment_structures")

    else:
        return render(request, "assessment_structures/assessment_structure_add.html")


@has_permission_required("r_assessment_structure")
def assessment_structure_edit(
    request, assessment_structure_id
):  # 3. view/edit Assessment Structure
    assessment_structure = Assessment_Structure.objects.get(id=assessment_structure_id)
    user_permissions = request.user.userprofile.role.permissions.values_list(
        "name", flat=True
    )
    if request.method == "POST":
        if "w_assessment_structure" not in user_permissions:
            raise PermissionDenied

        if request.POST.get("af_for"):
            af_for = request.POST.get("af_for")
            new_af_key = request.POST.get("custom_key")
            new_af_key = new_af_key.rstrip()

            if af_for == "summary":
                af_for_s = assessment_structure.s_fields or {}
                af_for_s[new_af_key] = ""
                assessment_structure.s_fields = af_for_s

            elif af_for == "additional_field":
                af_for_a = assessment_structure.a_fields or {}
                af_for_a[new_af_key] = ""
                assessment_structure.a_fields = af_for_a

            elif af_for == "vulnerability":
                af_for_v = assessment_structure.v_fields or {}
                af_for_v[new_af_key] = ""
                assessment_structure.v_fields = af_for_v

            assessment_structure.save()
            add_activity(
                request,
                "Assessment Structure Edited : " + str(assessment_structure.name),
            )
            return redirect(
                "assessment_structure_edit",
                assessment_structure_id=assessment_structure.id,
            )

        elif request.POST.get("as_name"):
            assessment_structure.name = Validation.validate_name(
                request.POST.get("as_name")
            )
            assessment_structure.description = request.POST.get("as_description")

            assessment_structure.save()
            add_activity(
                request,
                "Assessment Structure Edited : " + str(assessment_structure.name),
            )
            return redirect("assessment_structures")

        elif request.POST.get("template_action"):
            assessment_structure.template_name = Validation.validate_name(
                request.POST.get("t_name")
            )
            assessment_structure.template_about = request.POST.get("t_about")

            if request.POST.get("t_chart_settings"):
                assessment_structure.chart_settings = json.loads(
                    Validation.validate_json(request.POST.get("t_chart_settings"))
                )

            if "t_file" in request.FILES:
                validated_temp = Validation.validate_notRequired_docxFile(
                    request.FILES["t_file"]
                )
                if assessment_structure.template_file:
                    assessment_structure.template_file.delete()
                assessment_structure.template_file = validated_temp

            assessment_structure.save()
            add_activity(
                request,
                "Assessment Structure Template Updated : "
                + str(assessment_structure.name),
            )
            return redirect(
                "assessment_structure_edit",
                assessment_structure_id=assessment_structure.id,
            )

        else:
            raise BadRequest

    else:
        chart_settings_json = ""
        if assessment_structure.chart_settings:
            chart_settings_json = json.dumps(assessment_structure.chart_settings)
        else:
            chart_settings_json = """{"charts": [{"type": "pie","title": "Vulnerability Risk Distribution (Pie)","x_label": "","y_label": "","size": 120,"colors": {"Critical": "#c00000","High": "#ff0000","Medium": "#ffc000","Low": "#ffff00"}},{"type": "bar","title": "Vulnerability Risk Distribution (Bar)","x_label": "Risk Levels","y_label": "Count","size": 120,"colors": {"Critical": "#c00000","High": "#ff0000","Medium": "#ffc000","Low": "#ffff00"}}]}"""

        return render(
            request,
            "assessment_structures/assessment_structure_edit.html",
            {
                "assessment_structure": assessment_structure,
                "chart_settings_json": chart_settings_json,
            },
        )

        ## SAVE THE DATA INSIDE THE BOXES
        #     # Save af data --> work around
        #     summary_af = assessment_structure.s_fields or {}
        #     for key in summary_af:
        #         summary_af[key] = request.POST.get('s_' + key)
        #     assessment_af = assessment_structure.a_fields or {}
        #     for key in assessment_af:
        #         assessment_af[key] = request.POST.get('a_' + key)
        #     vulnerability_af = assessment_structure.v_fields or {}
        #     for key in vulnerability_af:
        #             vulnerability_af[key] = request.POST.get('v_' + key)

        #     assessment_structure.save()
        #     add_activity(request,"Assessment Structure Edited : " + str(assessment_structure.name))
        #     return redirect('assessment_structures')


@has_permission_required("w_assessment_structure")
def assessment_structure_delete(request):  # 4. delete assessment structure
    assessment_structure_id = request.POST.get("assessment_structure_id_delete")
    assessment_structure = Validation.validate_object(
        Assessment_Structure, assessment_structure_id
    )

    # Delete all the images in the ckeditor related to this assessment structure
    matching_ck_img_objects = CKImageUpload.objects.filter(
        for_model="Assessment_Structure", model_id=assessment_structure_id
    )
    for img in matching_ck_img_objects:
        img.image.delete()
        img.delete()

    assessment_structure.delete()
    add_activity(
        request, "Assessment Structure Deleted : " + str(assessment_structure.name)
    )
    return redirect("assessment_structures")


@has_permission_required("w_assessment_structure")
def assessment_structure_field_edit(request, assessment_structure_id, f_for, key):
    assessment_structure = Assessment_Structure.objects.get(id=assessment_structure_id)
    if request.method == "POST":
        if f_for == "s":
            assessment_structure.s_fields[key] = request.POST[key]
            assessment_structure.save()
            return redirect(
                "assessment_structure_edit",
                assessment_structure_id=assessment_structure.id,
            )

        elif f_for == "a":
            assessment_structure.a_fields[key] = request.POST[key]
            assessment_structure.save()
            return redirect(
                "assessment_structure_edit",
                assessment_structure_id=assessment_structure.id,
            )

        elif f_for == "v":
            assessment_structure.v_fields[key] = request.POST[key]
            assessment_structure.save()
            return redirect(
                "assessment_structure_edit",
                assessment_structure_id=assessment_structure.id,
            )
        else:
            raise BadRequest
    else:
        return render(
            request,
            "assessment_structures/assessment_structure_field_edit.html",
            {
                "assessment_structure": assessment_structure,
                "f_for": f_for,
                "key_to_edit": key,
            },
        )


@has_permission_required("w_assessment_structure")
def assessment_structure_field_delete(request):
    assessment_structure_id = request.POST.get("id")
    f_for = request.POST.get("for")
    key = request.POST.get("key")

    assessment_structure = Assessment_Structure.objects.get(id=assessment_structure_id)

    if f_for == "s":
        if key in assessment_structure.s_fields:
            del assessment_structure.s_fields[key]

    elif f_for == "a":
        if key in assessment_structure.a_fields:
            del assessment_structure.a_fields[key]

    elif f_for == "v":
        if key in assessment_structure.v_fields:
            del assessment_structure.v_fields[key]

    else:
        raise BadRequest

    assessment_structure.save()
    messages.success(request, "Field deleted: " + str(key))
    return redirect(
        "assessment_structure_edit", assessment_structure_id=assessment_structure.id
    )


@has_permission_required("r_assessment_structure")
def assessment_structure_template_download(request, assessment_structure_id):
    """Download template file from assessment structure"""
    assessment_structure = Assessment_Structure.objects.get(id=assessment_structure_id)
    if assessment_structure.template_file:
        return redirect(assessment_structure.template_file.url)
    else:
        messages.error(request, "No template file found")
        return redirect(
            "assessment_structure_edit", assessment_structure_id=assessment_structure.id
        )
