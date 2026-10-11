from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.shortcuts import get_object_or_404, render, redirect

from departments.models import Department
from doctors.models import Doctor
from patients.models import Patient, Visit
from system_settings.services import (
    get_next_patient_number,
    get_next_visit_number,
)


@login_required
def reception_dashboard(request):
    from django.utils import timezone

    today = timezone.localdate()

    patients_count = Patient.objects.filter(
        is_active=True
    ).count()

    patients_today = Patient.objects.filter(
        created_at__date=today,
        is_active=True
    ).count()

    visits_count = Visit.objects.count()

    visits_today = Visit.objects.filter(
        created_at__date=today
    ).count()

    departments = Department.objects.filter(
        is_active=True
    ).order_by("name_ar")

    recent_patients = Patient.objects.filter(
        is_active=True
    ).order_by("-created_at")[:10]

    recent_visits = Visit.objects.select_related(
        "patient",
        "department",
        "doctor"
    ).order_by("-created_at")[:10]

    context = {
        "stats": [
            ("إجمالي المرضى", patients_count, "👥"),
            ("مرضى اليوم", patients_today, "📅"),
            ("إجمالي الزيارات", visits_count, "🩺"),
            ("زيارات اليوم", visits_today, "🕐"),
        ],
        "patients_count": patients_count,
        "patients_today": patients_today,
        "visits_count": visits_count,
        "visits_today": visits_today,
        "departments": departments,
        "recent_patients": recent_patients,
        "recent_visits": recent_visits,
        "today": today,
    }

    return render(
        request,
        "reception/dashboard.html",
        context
    )

@login_required
def register_patient(request):

    if request.method == "POST":

        patient_number = request.POST.get("patient_number", "").strip()
        full_name = request.POST.get("full_name", "").strip()
        gender = request.POST.get("gender", "").strip()
        age_raw = request.POST.get("age", "").strip()
        age = None

        if age_raw:
            try:
                age = int(age_raw)
            except (TypeError, ValueError):
                messages.error(request, "العمر يجب أن يكون رقمًا صحيحًا.")
                return render(request, "reception/register_patient.html")

            if age < 0 or age > 150:
                messages.error(request, "يرجى إدخال عمر بين 0 و150 سنة.")
                return render(request, "reception/register_patient.html")

        if gender and gender not in {"M", "F", "O"}:
            messages.error(request, "قيمة الجنس غير صحيحة.")
            return render(request, "reception/register_patient.html")

        # ----------------------------------------------------
        # Central Patient Numbering
        # AUTO   -> generate centrally
        # MANUAL -> require user entry
        # ----------------------------------------------------
        generated_patient_number = get_next_patient_number()

        if generated_patient_number is not None:
            patient_number = generated_patient_number
        elif not patient_number:
            messages.error(
                request,
                "وضع ترقيم المرضى يدوي. يرجى إدخال رقم المريض."
            )
            return render(
                request,
                "reception/register_patient.html"
            )

        # منع تكرار رقم المريض
        if Patient.objects.filter(
            patient_number=patient_number
        ).exists():
            messages.error(
                request,
                f"رقم المريض {patient_number} مستخدم مسبقًا. يرجى إدخال رقم آخر."
            )
            return render(
                request,
                "reception/register_patient.html"
            )

        # التحقق من اسم المريض
        if not full_name:
            messages.error(
                request,
                "يرجى إدخال اسم المريض."
            )
            return render(
                request,
                "reception/register_patient.html"
            )

        patient = Patient.objects.create(
            patient_number=patient_number,
            full_name=full_name,
            gender=gender,
            age=age,
            phone=request.POST.get("phone"),
            address=request.POST.get("address"),
            national_id=request.POST.get("national_id"),
            emergency_contact_name=request.POST.get(
                "emergency_contact_name"
            ),
            emergency_contact_phone=request.POST.get(
                "emergency_contact_phone"
            ),
            blood_group=request.POST.get("blood_group"),
            allergies=request.POST.get("allergies"),
            medical_notes=request.POST.get("medical_notes"),
        )

        messages.success(
            request,
            f"تم تسجيل المريض {patient.full_name} بنجاح. رقم الملف: {patient.patient_number}"
        )

        return redirect(
            "reception:dashboard"
        )

    return render(
        request,
        "reception/register_patient.html"
    )


@login_required
def patient_search(request):
    query = request.GET.get("q", "").strip()

    patients = Patient.objects.none()

    if query:
        patients = Patient.objects.filter(
            is_active=True
        ).filter(
            models.Q(patient_number__icontains=query) |
            models.Q(full_name__icontains=query) |
            models.Q(phone__icontains=query) |
            models.Q(national_id__icontains=query)
        )

    return render(
        request,
        "reception/patient_search.html",
        {
            "patients": patients,
            "query": query,
        }
    )


@login_required
def patient_profile(request, patient_id):
    patient = get_object_or_404(
        Patient,
        id=patient_id
    )

    visits = patient.visits.all()

    return render(
        request,
        "reception/patient_profile.html",
        {
            "patient": patient,
            "visits": visits,
        }
    )

from departments.models import Department
from doctors.models import Doctor


@login_required
def create_visit(request, patient_id):

    patient = get_object_or_404(
        Patient,
        id=patient_id
    )

    departments = Department.objects.filter(
        is_active=True
    ).order_by("name_ar")

    selected_department = request.GET.get("department")

    doctors = Doctor.objects.filter(
        is_active=True
    ).select_related(
        "department"
    ).order_by("full_name")

    if selected_department:
        doctors = doctors.filter(
            department_id=selected_department
        )

    if request.method == "POST":

        visit_number = request.POST.get(
            "visit_number",
            ""
        ).strip()

        visit_type = request.POST.get(
            "visit_type",
            "OPD"
        )

        department_id = request.POST.get(
            "department"
        )

        doctor_id = request.POST.get(
            "doctor"
        )

        reason = request.POST.get(
            "reason",
            ""
        ).strip()

        referring_doctor = request.POST.get(
            "referring_doctor",
            ""
        ).strip()

        notes = request.POST.get(
            "notes",
            ""
        ).strip()

        # ------------------------------------------
        # التحقق من القسم
        # ------------------------------------------

        if not department_id:

            messages.error(
                request,
                "يجب اختيار القسم."
            )

            return redirect(
                "reception:create_visit",
                patient_id=patient.id
            )

        department = get_object_or_404(
            Department,
            id=department_id,
            is_active=True
        )

        # ------------------------------------------
        # التحقق من الطبيب
        # ------------------------------------------

        if not doctor_id:

            messages.error(
                request,
                "يجب اختيار الطبيب."
            )

            return redirect(
                "reception:create_visit",
                patient_id=patient.id
            )

        doctor = get_object_or_404(
            Doctor,
            id=doctor_id,
            is_active=True
        )

        # ------------------------------------------
        # التأكد أن الطبيب تابع للقسم
        # ------------------------------------------

        if doctor.department_id != department.id:

            messages.error(
                request,
                "الطبيب المختار لا يتبع القسم المحدد."
            )

            return redirect(
                "reception:create_visit",
                patient_id=patient.id
            )

        # ------------------------------------------
        # Central Visit Numbering
        # If empty, generate automatically.
        # ------------------------------------------

        if not visit_number:
            visit_number = get_next_visit_number()

        if not visit_number:
            messages.error(
                request,
                "تعذر إنشاء رقم الزيارة تلقائيًا."
            )

            return redirect(
                "reception:create_visit",
                patient_id=patient.id
            )

        if Visit.objects.filter(
            visit_number=visit_number
        ).exists():

            messages.error(
                request,
                "رقم الزيارة مستخدم مسبقًا."
            )

            return redirect(
                "reception:create_visit",
                patient_id=patient.id
            )

        # ------------------------------------------
        # إنشاء الزيارة
        # ------------------------------------------

        Visit.objects.create(
            patient=patient,
            visit_number=visit_number,
            visit_type=visit_type,
            department=department,
            doctor=doctor,
            reason=reason,
            referring_doctor=referring_doctor,
            notes=notes,
        )

        messages.success(
            request,
            "تم إنشاء الزيارة وربطها بالقسم والطبيب بنجاح."
        )

        return redirect(
            "reception:patient_profile",
            patient_id=patient.id
        )

    return render(
        request,
        "reception/create_visit.html",
        {
            "patient": patient,
            "departments": departments,
            "doctors": doctors,
            "selected_department": selected_department,
        }
    )
