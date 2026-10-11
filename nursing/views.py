from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.permissions import get_user_role
from patients.models import Patient, Visit
from laboratory.models import LaboratoryOrder

from .forms import (
    NursingAssessmentForm,
    VitalSignsForm,
    NursingNoteForm,
    MedicationAdministrationForm,
    NursingCarePlanForm,
)
from .models import (
    NursingAssessment,
    VitalSigns,
    NursingNote,
    MedicationAdministration,
    NursingCarePlan,
)


@login_required
def dashboard(request):
    role = get_user_role(request.user)
    today = timezone.localdate()

    context = {
        "role": role,
        "today": today,
        "total_patients": Patient.objects.count(),
        "today_visits": Visit.objects.filter(
            created_at__date=today
        ).count(),
        "today_lab_orders": LaboratoryOrder.objects.filter(
            requested_at__date=today
        ).count(),
        "today_assessments": NursingAssessment.objects.filter(
            created_at__date=today
        ).count(),
        "today_vitals": VitalSigns.objects.filter(
            recorded_at__date=today
        ).count(),
        "today_notes": NursingNote.objects.filter(
            created_at__date=today
        ).count(),
        "today_medications": MedicationAdministration.objects.filter(
            administration_time__date=today
        ).count(),
        "active_care_plans": NursingCarePlan.objects.filter(
            status="ACTIVE"
        ).count(),
        "recent_assessments": NursingAssessment.objects.select_related(
            "patient",
            "nurse",
        )[:10],
        "recent_vitals": VitalSigns.objects.select_related(
            "patient",
            "recorded_by",
        )[:10],
    }

    return render(
        request,
        "nursing/dashboard.html",
        context,
    )


@login_required
def patient_list(request):
    q = request.GET.get("q", "").strip()

    patients = Patient.objects.all()

    if q:
        patients = patients.filter(
            Q(full_name__icontains=q)
            | Q(patient_number__icontains=q)
            | Q(phone__icontains=q)
        )

    patients = patients.order_by("full_name")[:200]

    return render(
        request,
        "nursing/patient_list.html",
        {
            "patients": patients,
            "q": q,
        },
    )


@login_required
def patient_record(request, patient_id):
    patient = get_object_or_404(
        Patient,
        id=patient_id,
    )

    assessments = NursingAssessment.objects.filter(
        patient=patient
    ).select_related(
        "visit",
        "nurse",
    )[:20]

    vitals = VitalSigns.objects.filter(
        patient=patient
    ).select_related(
        "visit",
        "recorded_by",
    )[:30]

    notes = NursingNote.objects.filter(
        patient=patient
    ).select_related(
        "visit",
        "nurse",
    )[:20]

    medications = MedicationAdministration.objects.filter(
        patient=patient
    ).select_related(
        "visit",
        "administered_by",
    )[:20]

    care_plans = NursingCarePlan.objects.filter(
        patient=patient
    ).select_related(
        "visit",
        "created_by",
    )[:20]

    return render(
        request,
        "nursing/patient_record.html",
        {
            "patient": patient,
            "assessments": assessments,
            "vitals": vitals,
            "notes": notes,
            "medications": medications,
            "care_plans": care_plans,
        },
    )


@login_required
def assessment_create(request):
    if request.method == "POST":
        form = NursingAssessmentForm(request.POST)

        if form.is_valid():
            assessment = form.save(commit=False)
            assessment.nurse = request.user
            assessment.save()

            messages.success(
                request,
                "تم حفظ التقييم التمريضي بنجاح.",
            )

            return redirect(
                "nursing:patient_record",
                patient_id=assessment.patient_id,
            )
    else:
        form = NursingAssessmentForm()

    return render(
        request,
        "nursing/assessment_form.html",
        {
            "form": form,
            "title": "تقييم تمريضي جديد",
        },
    )


@login_required
def vital_signs_create(request):
    if request.method == "POST":
        form = VitalSignsForm(request.POST)

        if form.is_valid():
            vital = form.save(commit=False)
            vital.recorded_by = request.user
            vital.save()

            messages.success(
                request,
                "تم تسجيل العلامات الحيوية بنجاح.",
            )

            return redirect(
                "nursing:patient_record",
                patient_id=vital.patient_id,
            )
    else:
        form = VitalSignsForm()

    return render(
        request,
        "nursing/vitals_form.html",
        {
            "form": form,
            "title": "تسجيل العلامات الحيوية",
        },
    )


@login_required
def note_create(request):
    if request.method == "POST":
        form = NursingNoteForm(request.POST)

        if form.is_valid():
            note = form.save(commit=False)
            note.nurse = request.user
            note.save()

            messages.success(
                request,
                "تم حفظ ملاحظة التمريض بنجاح.",
            )

            return redirect(
                "nursing:patient_record",
                patient_id=note.patient_id,
            )
    else:
        form = NursingNoteForm()

    return render(
        request,
        "nursing/note_form.html",
        {
            "form": form,
            "title": "ملاحظة تمريضية جديدة",
        },
    )


@login_required
def medication_create(request):
    if request.method == "POST":
        form = MedicationAdministrationForm(request.POST)

        if form.is_valid():
            medication = form.save(commit=False)
            medication.administered_by = request.user
            medication.save()

            messages.success(
                request,
                "تم تسجيل إعطاء الدواء بنجاح.",
            )

            return redirect(
                "nursing:patient_record",
                patient_id=medication.patient_id,
            )
    else:
        form = MedicationAdministrationForm(
            initial={
                "administration_time": timezone.localtime().strftime(
                    "%Y-%m-%dT%H:%M"
                )
            }
        )

    return render(
        request,
        "nursing/medication_form.html",
        {
            "form": form,
            "title": "تسجيل إعطاء دواء",
        },
    )


@login_required
def care_plan_create(request):
    if request.method == "POST":
        form = NursingCarePlanForm(request.POST)

        if form.is_valid():
            care_plan = form.save(commit=False)
            care_plan.created_by = request.user
            care_plan.save()

            messages.success(
                request,
                "تم حفظ خطة الرعاية التمريضية بنجاح.",
            )

            return redirect(
                "nursing:patient_record",
                patient_id=care_plan.patient_id,
            )
    else:
        form = NursingCarePlanForm()

    return render(
        request,
        "nursing/care_plan_form.html",
        {
            "form": form,
            "title": "خطة رعاية تمريضية جديدة",
        },
    )
