from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .models import ClinicalDiagnosis, Patient, Visit
from .forms import ClinicalDiagnosisForm, PatientForm, VisitForm
from departments.models import Department
from accounts.permissions import (
    get_user_role,
    get_user_department,
    user_has_access,
    user_has_permission,
)


def _allowed(user, permission):
    return user_has_permission(user, permission)

def _department_id_conflicts(request):
    get_id = request.GET.get("department_id")
    post_id = (
        request.POST.get("department_id")
        if request.method == "POST"
        else None
    )
    return bool(
        get_id
        and post_id
        and str(get_id).strip() != str(post_id).strip()
    )



@login_required
def patient_list(request):
    if not _allowed(request.user, "patients.view"):
        messages.error(request, "ليس لديك صلاحية عرض المرضى.")
        return redirect("/")

    query = request.GET.get("q", "").strip()

    patients = Patient.objects.filter(
        is_active=True
    ).order_by("-created_at")

    if query:
        patients = patients.filter(
            Q(patient_number__icontains=query)
            | Q(full_name__icontains=query)
            | Q(phone__icontains=query)
            | Q(national_id__icontains=query)
        )

    return render(
        request,
        "patients/patient_list.html",
        {
            "patients": patients,
            "query": query,
            "role": get_user_role(request.user),
        },
    )


@login_required
def patient_search(request):
    if not _allowed(request.user, "patients.view"):
        messages.error(request, "ليس لديك صلاحية البحث عن المرضى.")
        return redirect("/")

    query = request.GET.get("q", "").strip()

    patients = Patient.objects.all().order_by("-created_at")

    if query:
        patients = patients.filter(
            Q(patient_number__icontains=query)
            | Q(full_name__icontains=query)
            | Q(phone__icontains=query)
            | Q(national_id__icontains=query)
        )

    return render(
        request,
        "patients/patient_search.html",
        {
            "patients": patients,
            "query": query,
        },
    )


@login_required
def patient_create(request):
    if not _allowed(request.user, "patients.create"):
        messages.error(request, "ليس لديك صلاحية إضافة مريض.")
        return redirect("/patients/")

    if _department_id_conflicts(request):
        messages.error(
            request,
            "رقم القسم في الصفحة لا يطابق القسم المرسل في النموذج.",
        )
        return redirect("/patients/")

    requested_department_id = (
        request.GET.get("department_id")
        or request.POST.get("department_id")
    )
    selected_department = None

    if requested_department_id:
        try:
            selected_department = Department.objects.get(
                pk=requested_department_id,
                is_active=True,
            )
        except (Department.DoesNotExist, ValueError, TypeError):
            messages.error(request, "القسم المحدد غير موجود أو غير نشط.")
            return redirect("/patients/")

        role = get_user_role(request.user)
        is_manager = (
            request.user.is_superuser
            or role in ("ADMIN", "MANAGER")
        )
        user_department = get_user_department(request.user)

        if (
            not user_has_access(request.user, "departments")
            or (
                not is_manager
                and (
                    not user_department
                    or user_department.pk != selected_department.pk
                )
            )
        ):
            messages.error(
                request,
                "ليس لديك صلاحية تسجيل مريض من هذا القسم.",
            )
            return redirect("/patients/")

    if request.method == "POST":
        form = PatientForm(request.POST)

        if form.is_valid():
            patient = form.save()
            messages.success(
                request,
                f"تم تسجيل المريض {patient.full_name} بنجاح.",
            )

            if selected_department:
                from django.urls import reverse
                visit_url = reverse(
                    "patients:visit_create",
                    kwargs={"patient_id": patient.id},
                )
                return redirect(
                    f"{visit_url}?department_id={selected_department.pk}"
                )

            return redirect(
                "patients:detail",
                patient_id=patient.id,
            )
    else:
        form = PatientForm(
            initial={"is_active": True}
        )

    return render(
        request,
        "patients/patient_form.html",
        {
            "form": form,
            "title": "تسجيل مريض جديد",
            "department": selected_department,
        },
    )

@login_required
def patient_edit(request, patient_id):
    if not _allowed(request.user, "patients.edit"):
        messages.error(request, "ليس لديك صلاحية تعديل بيانات المريض.")
        return redirect("/patients/")

    patient = get_object_or_404(Patient, pk=patient_id)

    if request.method == "POST":
        form = PatientForm(request.POST, instance=patient)

        if form.is_valid():
            form.save()
            messages.success(request, "تم تحديث بيانات المريض بنجاح.")
            return redirect(
                "patients:detail",
                patient_id=patient.id,
            )
    else:
        form = PatientForm(instance=patient)

    return render(
        request,
        "patients/patient_form.html",
        {
            "form": form,
            "title": "تعديل بيانات المريض",
            "patient": patient,
        },
    )


@login_required
def patient_detail(request, patient_id):
    if not _allowed(request.user, "patients.view"):
        messages.error(request, "ليس لديك صلاحية عرض ملف المريض.")
        return redirect("/")

    patient = get_object_or_404(
        Patient.objects.prefetch_related(
            "visits__department",
            "visits__doctor",
        ),
        pk=patient_id,
    )

    visits = patient.visits.all().order_by("-created_at")

    return render(
        request,
        "patients/patient_detail.html",
        {
            "patient": patient,
            "visits": visits,
        },
    )


@login_required
def patient_visits(request, patient_id):
    if not _allowed(request.user, "patients.view"):
        messages.error(request, "ليس لديك صلاحية عرض زيارات المريض.")
        return redirect("/")

    patient = get_object_or_404(Patient, pk=patient_id)

    visits = Visit.objects.filter(
        patient=patient
    ).select_related(
        "department",
        "doctor",
    ).order_by("-created_at")

    return render(
        request,
        "patients/patient_visits.html",
        {
            "patient": patient,
            "visits": visits,
        },
    )


@login_required
def visit_create(request, patient_id):
    if not _allowed(request.user, "patients.create"):
        messages.error(request, "ليس لديك صلاحية إنشاء زيارة.")
        return redirect("patients:detail", patient_id=patient_id)

    patient = get_object_or_404(Patient, pk=patient_id)

    if _department_id_conflicts(request):
        messages.error(
            request,
            "رقم القسم في الصفحة لا يطابق القسم المرسل في النموذج.",
        )
        return redirect("patients:detail", patient_id=patient_id)

    requested_department_id = (
        request.GET.get("department_id")
        or request.POST.get("department_id")
    )
    selected_department = None

    if requested_department_id:
        try:
            selected_department = Department.objects.get(
                pk=requested_department_id,
                is_active=True,
            )
        except (Department.DoesNotExist, ValueError, TypeError):
            messages.error(request, "القسم المحدد غير موجود أو غير نشط.")
            return redirect("patients:detail", patient_id=patient_id)

        role = get_user_role(request.user)
        is_manager = (
            request.user.is_superuser
            or role in ("ADMIN", "MANAGER")
        )
        user_department = get_user_department(request.user)

        if (
            not user_has_access(request.user, "departments")
            or (
                not is_manager
                and (
                    not user_department
                    or user_department.pk != selected_department.pk
                )
            )
        ):
            messages.error(
                request,
                "ليس لديك صلاحية إنشاء زيارة في هذا القسم.",
            )
            return redirect("patients:detail", patient_id=patient_id)

    if request.method == "POST":
        form = VisitForm(request.POST, fixed_department=selected_department)

        if form.is_valid():
            submitted_department = form.cleaned_data.get("department")

            if (
                selected_department
                and (
                    not submitted_department
                    or submitted_department.pk != selected_department.pk
                )
            ):
                form.add_error(
                    "department",
                    "يجب أن يبقى القسم مطابقًا للقسم الذي بدأت منه الزيارة.",
                )
            else:
                visit = form.save(commit=False)
                visit.patient = patient
                visit.save()

                messages.success(
                    request,
                    f"تم إنشاء الزيارة رقم {visit.visit_number} بنجاح.",
                )
                return redirect(
                    "patients:visit_detail",
                    visit_id=visit.id,
                )
    else:
        initial = {"status": "OPEN"}
        if selected_department:
            initial["department"] = selected_department.pk
        form = VisitForm(initial=initial, fixed_department=selected_department)

    return render(
        request,
        "patients/visit_form.html",
        {
            "form": form,
            "patient": patient,
            "title": "إنشاء زيارة جديدة",
            "department": selected_department,
        },
    )


@login_required
def diagnosis_create(request, visit_id):
    if not _allowed(request.user, "patients.create"):
        messages.error(request, "ليس لديك صلاحية تسجيل تشخيص.")
        return redirect("patients:visit_detail", visit_id=visit_id)

    visit = get_object_or_404(
        Visit.objects.select_related(
            "patient",
            "department",
            "doctor",
        ),
        pk=visit_id,
    )

    if request.method == "POST":
        form = ClinicalDiagnosisForm(
            request.POST,
            patient=visit.patient,
            visit=visit,
            department=visit.department,
            doctor=visit.doctor,
        )

        if form.is_valid():
            diagnosis = form.save(commit=False)
            diagnosis.patient = visit.patient
            diagnosis.visit = visit
            diagnosis.department = visit.department
            diagnosis.doctor = visit.doctor
            diagnosis.save()

            messages.success(
                request,
                f"تم تسجيل التشخيص «{diagnosis.diagnosis_name}» بنجاح."
            )

            return redirect(
                "patients:visit_detail",
                visit_id=visit.id,
            )
    else:
        form = ClinicalDiagnosisForm(
            patient=visit.patient,
            visit=visit,
            department=visit.department,
            doctor=visit.doctor,
        )

    return render(
        request,
        "patients/diagnosis_form.html",
        {
            "form": form,
            "visit": visit,
            "patient": visit.patient,
        },
    )


@login_required
def visit_detail(request, visit_id):
    if not _allowed(request.user, "patients.view"):
        messages.error(request, "ليس لديك صلاحية عرض الزيارة.")
        return redirect("/")

    visit = get_object_or_404(
        Visit.objects.select_related(
            "patient",
            "department",
            "doctor",
        ),
        pk=visit_id,
    )

    laboratory_orders = []

    try:
        from laboratory.models import LaboratoryOrder

        laboratory_orders = LaboratoryOrder.objects.filter(
            visit=visit
        ).prefetch_related(
            "items__test"
        ).order_by("-requested_at")
    except Exception:
        laboratory_orders = []

    diagnoses = ClinicalDiagnosis.objects.filter(
        visit=visit
    ).select_related(
        "department",
        "doctor",
    ).order_by("-created_at")

    return render(
        request,
        "patients/visit_detail.html",
        {
            "visit": visit,
            "laboratory_orders": laboratory_orders,
            "diagnoses": diagnoses,
        },
    )
