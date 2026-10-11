from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from patients.models import Patient
from doctors.models import Doctor
from departments.models import Department

from .models import EmergencyCase


def make_case_number():
    last = EmergencyCase.objects.order_by("-id").first()

    if not last:
        number = 1
    else:
        number = last.id + 1

    return f"ER-{number:06d}"


@login_required
def emergency_dashboard(request):

    cases = EmergencyCase.objects.select_related(
        "patient",
        "doctor",
        "department",
    )

    context = {
        "total_cases": cases.count(),
        "waiting_cases": cases.filter(status="WAITING").count(),
        "under_care": cases.filter(status="UNDER_CARE").count(),
        "observation": cases.filter(status="OBSERVATION").count(),
        "admitted": cases.filter(status="ADMITTED").count(),
        "today_cases": cases.filter(
            arrival_at__date=timezone.localdate()
        ).count(),
        "recent_cases": cases[:20],
    }

    return render(
        request,
        "emergency/dashboard.html",
        context,
    )


@login_required
def emergency_case_create(request):

    if request.method == "POST":

        patient_id = request.POST.get("patient")
        doctor_id = request.POST.get("doctor") or None
        triage_level = request.POST.get("triage_level", "YELLOW")

        patient = get_object_or_404(
            Patient,
            id=patient_id,
        )

        doctor = None

        if doctor_id:
            doctor = get_object_or_404(
                Doctor,
                id=doctor_id,
            )

        emergency_department = Department.objects.filter(
            code="ER"
        ).first()

        case = EmergencyCase.objects.create(
            case_number=make_case_number(),
            patient=patient,
            doctor=doctor,
            department=emergency_department,
            triage_level=triage_level,
            chief_complaint=request.POST.get(
                "chief_complaint",
                "",
            ).strip(),
            history=request.POST.get(
                "history",
                "",
            ).strip(),
            temperature=request.POST.get("temperature") or None,
            pulse=request.POST.get("pulse") or None,
            respiratory_rate=request.POST.get(
                "respiratory_rate"
            ) or None,
            systolic_bp=request.POST.get(
                "systolic_bp"
            ) or None,
            diastolic_bp=request.POST.get(
                "diastolic_bp"
            ) or None,
            oxygen_saturation=request.POST.get(
                "oxygen_saturation"
            ) or None,
            pain_score=request.POST.get(
                "pain_score"
            ) or None,
            preliminary_diagnosis=request.POST.get(
                "preliminary_diagnosis",
                "",
            ).strip(),
            treatment=request.POST.get(
                "treatment",
                "",
            ).strip(),
            clinical_notes=request.POST.get(
                "clinical_notes",
                "",
            ).strip(),
            registered_by=request.user,
        )

        messages.success(
            request,
            f"تم تسجيل حالة الطوارئ {case.case_number} بنجاح.",
        )

        return redirect(
            "emergency:detail",
            case_id=case.id,
        )

    patients = Patient.objects.filter(
        is_active=True
    ).order_by("full_name")

    doctors = Doctor.objects.filter(
        is_active=True
    ).order_by("full_name")

    return render(
        request,
        "emergency/case_form.html",
        {
            "patients": patients,
            "doctors": doctors,
            "triage_choices": EmergencyCase.TRIAGE_CHOICES,
        },
    )


@login_required
def emergency_case_detail(request, case_id):

    case = get_object_or_404(
        EmergencyCase.objects.select_related(
            "patient",
            "doctor",
            "department",
            "registered_by",
        ),
        id=case_id,
    )

    return render(
        request,
        "emergency/case_detail.html",
        {
            "case": case,
        },
    )


@login_required
def emergency_case_update(request, case_id):

    case = get_object_or_404(
        EmergencyCase,
        id=case_id,
    )

    if request.method == "POST":

        case.triage_level = request.POST.get(
            "triage_level",
            case.triage_level,
        )

        case.status = request.POST.get(
            "status",
            case.status,
        )

        case.disposition = request.POST.get(
            "disposition",
            case.disposition,
        )

        case.preliminary_diagnosis = request.POST.get(
            "preliminary_diagnosis",
            "",
        ).strip()

        case.treatment = request.POST.get(
            "treatment",
            "",
        ).strip()

        case.clinical_notes = request.POST.get(
            "clinical_notes",
            "",
        ).strip()

        if case.status == "UNDER_CARE" and not case.treated_at:
            case.treated_at = timezone.now()

        if case.status == "DISCHARGED":
            case.discharged_at = timezone.now()

        case.save()

        messages.success(
            request,
            "تم تحديث حالة الطوارئ.",
        )

        return redirect(
            "emergency:detail",
            case_id=case.id,
        )

    return render(
        request,
        "emergency/case_update.html",
        {
            "case": case,
            "triage_choices": EmergencyCase.TRIAGE_CHOICES,
            "status_choices": EmergencyCase.STATUS_CHOICES,
            "disposition_choices": EmergencyCase.DISPOSITION_CHOICES,
        },
    )


@login_required
def emergency_search(request):

    query = request.GET.get(
        "q",
        "",
    ).strip()

    cases = EmergencyCase.objects.select_related(
        "patient",
        "doctor",
    )

    if query:
        from django.db.models import Q

        cases = cases.filter(
            Q(case_number__icontains=query)
            | Q(patient__full_name__icontains=query)
            | Q(patient__patient_number__icontains=query)
        )

    return render(
        request,
        "emergency/search.html",
        {
            "cases": cases[:100],
            "query": query,
        },
    )
