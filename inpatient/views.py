from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from patients.models import Patient, Visit
from departments.models import Department
from doctors.models import Doctor

from .models import (
    Room,
    Bed,
    Admission,
    BedTransfer,
    InpatientNote,
    InpatientVitalSign,
)


def is_manager(user):
    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    try:
        return user.staff_profile.role in ["ADMIN", "MANAGER"]
    except Exception:
        return False


def make_admission_number():
    last = Admission.objects.order_by("-id").first()

    if not last:
        number = 1
    else:
        number = last.id + 1

    return f"ADM-{number:06d}"


@login_required
def inpatient_dashboard(request):
    today = timezone.localtime().date()

    total_rooms = Room.objects.filter(is_active=True).count()
    total_beds = Bed.objects.filter(status__in=["AVAILABLE", "OCCUPIED", "RESERVED"]).count()
    available_beds = Bed.objects.filter(status="AVAILABLE").count()
    occupied_beds = Bed.objects.filter(status="OCCUPIED").count()

    active_admissions = Admission.objects.filter(
        status="ADMITTED"
    ).select_related(
        "patient",
        "department",
        "doctor",
        "room",
        "bed",
    )

    today_admissions = Admission.objects.filter(
        admitted_at__date=today
    ).count()

    today_discharges = Admission.objects.filter(
        discharged_at__date=today
    ).count()

    context = {
        "total_rooms": total_rooms,
        "total_beds": total_beds,
        "available_beds": available_beds,
        "occupied_beds": occupied_beds,
        "today_admissions": today_admissions,
        "today_discharges": today_discharges,
        "active_admissions": active_admissions[:20],
    }

    return render(
        request,
        "inpatient/dashboard.html",
        context,
    )


@login_required
def room_list(request):
    rooms = Room.objects.select_related("department").all()

    return render(
        request,
        "inpatient/room_list.html",
        {
            "rooms": rooms,
            "can_manage": is_manager(request.user),
        },
    )


@login_required
def room_create(request):
    if not is_manager(request.user):
        messages.error(request, "ليس لديك صلاحية إضافة الغرف.")
        return redirect("inpatient:room_list")

    departments = Department.objects.filter(is_active=True)

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        room_number = request.POST.get("room_number", "").strip()
        room_type = request.POST.get("room_type", "GENERAL")
        department_id = request.POST.get("department")
        floor = request.POST.get("floor", "").strip()
        capacity = request.POST.get("capacity", "1")
        phone = request.POST.get("phone", "").strip()
        notes = request.POST.get("notes", "").strip()

        if not name or not room_number:
            messages.error(request, "يرجى إدخال اسم الغرفة ورقم الغرفة.")
        elif Room.objects.filter(room_number=room_number).exists():
            messages.error(request, "رقم الغرفة مستخدم بالفعل.")
        else:
            department = None

            if department_id:
                department = Department.objects.filter(
                    id=department_id
                ).first()

            try:
                capacity_value = max(1, int(capacity))
            except (TypeError, ValueError):
                capacity_value = 1

            Room.objects.create(
                name=name,
                room_number=room_number,
                room_type=room_type,
                department=department,
                floor=floor,
                capacity=capacity_value,
                phone=phone,
                notes=notes,
            )

            messages.success(request, "تمت إضافة الغرفة بنجاح.")
            return redirect("inpatient:room_list")

    return render(
        request,
        "inpatient/room_form.html",
        {
            "room": None,
            "departments": departments,
            "room_types": Room.ROOM_TYPES,
        },
    )


@login_required
def room_edit(request, room_id):
    if not is_manager(request.user):
        messages.error(request, "ليس لديك صلاحية تعديل الغرف.")
        return redirect("inpatient:room_list")

    room = get_object_or_404(Room, id=room_id)
    departments = Department.objects.filter(is_active=True)

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        room_number = request.POST.get("room_number", "").strip()
        room_type = request.POST.get("room_type", "GENERAL")
        department_id = request.POST.get("department")
        floor = request.POST.get("floor", "").strip()
        capacity = request.POST.get("capacity", "1")
        phone = request.POST.get("phone", "").strip()
        notes = request.POST.get("notes", "").strip()

        duplicate = Room.objects.filter(
            room_number=room_number
        ).exclude(id=room.id).exists()

        if not name or not room_number:
            messages.error(request, "يرجى إدخال اسم الغرفة ورقم الغرفة.")
        elif duplicate:
            messages.error(request, "رقم الغرفة مستخدم بالفعل.")
        else:
            room.name = name
            room.room_number = room_number
            room.room_type = room_type
            room.department = (
                Department.objects.filter(id=department_id).first()
                if department_id
                else None
            )
            room.floor = floor

            try:
                room.capacity = max(1, int(capacity))
            except (TypeError, ValueError):
                room.capacity = 1

            room.phone = phone
            room.notes = notes
            room.save()

            messages.success(request, "تم تعديل الغرفة بنجاح.")
            return redirect("inpatient:room_list")

    return render(
        request,
        "inpatient/room_form.html",
        {
            "room": room,
            "departments": departments,
            "room_types": Room.ROOM_TYPES,
        },
    )


@login_required
def bed_list(request):
    beds = Bed.objects.select_related(
        "room",
        "room__department",
    ).all()

    return render(
        request,
        "inpatient/bed_list.html",
        {
            "beds": beds,
            "can_manage": is_manager(request.user),
        },
    )


@login_required
def bed_create(request):
    if not is_manager(request.user):
        messages.error(request, "ليس لديك صلاحية إضافة الأسرة.")
        return redirect("inpatient:bed_list")

    rooms = Room.objects.filter(is_active=True)

    if request.method == "POST":
        room_id = request.POST.get("room")
        bed_number = request.POST.get("bed_number", "").strip()
        notes = request.POST.get("notes", "").strip()

        room = Room.objects.filter(
            id=room_id,
            is_active=True,
        ).first()

        if not room:
            messages.error(request, "الغرفة المحددة غير موجودة.")
        elif not bed_number:
            messages.error(request, "يرجى إدخال رقم السرير.")
        elif Bed.objects.filter(
            room=room,
            bed_number=bed_number,
        ).exists():
            messages.error(request, "رقم السرير مستخدم داخل هذه الغرفة.")
        else:
            Bed.objects.create(
                room=room,
                bed_number=bed_number,
                notes=notes,
            )

            messages.success(request, "تمت إضافة السرير بنجاح.")
            return redirect("inpatient:bed_list")

    return render(
        request,
        "inpatient/bed_form.html",
        {
            "rooms": rooms,
        },
    )


@login_required
def admission_list(request):
    """
    سجل التنويم:
    - البحث باسم المريض
    - البحث برقم المريض
    - البحث برقم التنويم
    - البحث برقم الهاتف
    - فلترة حسب حالة التنويم
    """

    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()

    admissions = Admission.objects.select_related(
        "patient",
        "department",
        "doctor",
        "room",
        "bed",
        "visit",
    ).order_by("-admitted_at")

    if query:
        admissions = admissions.filter(
            Q(patient__full_name__icontains=query)
            | Q(patient__patient_number__icontains=query)
            | Q(admission_number__icontains=query)
            | Q(patient__phone__icontains=query)
        )

    valid_statuses = {
        choice[0]
        for choice in Admission.STATUS_CHOICES
    }

    if status in valid_statuses:
        admissions = admissions.filter(status=status)

    total_count = admissions.count()
    active_count = admissions.filter(status="ADMITTED").count()
    discharged_count = admissions.filter(status="DISCHARGED").count()
    transferred_count = admissions.filter(status="TRANSFERRED").count()

    context = {
        "admissions": admissions,
        "query": query,
        "selected_status": status,
        "status_choices": Admission.STATUS_CHOICES,

        "total_count": total_count,
        "active_count": active_count,
        "discharged_count": discharged_count,
        "transferred_count": transferred_count,
    }

    return render(
        request,
        "inpatient/admission_list.html",
        context,
    )


@login_required
def patient_visits_api(request):
    """
    إرجاع زيارات المريض بصيغة JSON لاستخدامها في نموذج التنويم.
    """
    patient_id = request.GET.get("patient_id", "").strip()

    if not patient_id:
        return JsonResponse({
            "success": True,
            "visits": [],
        })

    patient = Patient.objects.filter(
        id=patient_id,
        is_active=True,
    ).first()

    if not patient:
        return JsonResponse({
            "success": False,
            "message": "المريض غير موجود.",
            "visits": [],
        }, status=404)

    visits = Visit.objects.filter(
        patient=patient,
    ).select_related(
        "department",
        "doctor",
    ).order_by("-created_at")[:50]

    data = []

    for visit in visits:
        data.append({
            "id": visit.id,
            "visit_number": visit.visit_number,
            "visit_type": visit.get_visit_type_display(),
            "visit_type_code": visit.visit_type,
            "status": visit.get_status_display(),
            "status_code": visit.status,
            "department_id": visit.department_id,
            "department_name": (
                visit.department.name_ar
                if visit.department
                else ""
            ),
            "department_name_en": (
                visit.department.name_en
                if visit.department
                else ""
            ),
            "doctor_id": visit.doctor_id,
            "doctor_name": (
                visit.doctor.full_name
                if visit.doctor
                else ""
            ),
            "reason": visit.reason or "",
            "created_at": (
                visit.created_at.strftime("%Y-%m-%d %H:%M")
                if visit.created_at
                else ""
            ),
        })

    return JsonResponse({
        "success": True,
        "patient": {
            "id": patient.id,
            "patient_number": patient.patient_number,
            "full_name": patient.full_name,
        },
        "visits": data,
    })


@login_required
def admission_create(request):
    patients = Patient.objects.filter(is_active=True)
    departments = Department.objects.filter(is_active=True)
    doctors = Doctor.objects.filter(is_active=True).select_related("department")

    beds = Bed.objects.filter(
        status="AVAILABLE",
        room__is_active=True,
    ).select_related(
        "room",
        "room__department",
    )

    if request.method == "POST":
        patient_id = request.POST.get("patient", "").strip()
        visit_id = request.POST.get("visit", "").strip()
        department_id = request.POST.get("department", "").strip()
        doctor_id = request.POST.get("doctor", "").strip()
        bed_id = request.POST.get("bed", "").strip()

        admission_type = request.POST.get(
            "admission_type",
            "EMERGENCY",
        )

        expected_discharge_date_raw = request.POST.get(
            "expected_discharge_date",
            "",
        ).strip()

        diagnosis = request.POST.get(
            "admission_diagnosis",
            "",
        ).strip()

        clinical_notes = request.POST.get(
            "clinical_notes",
            "",
        ).strip()

        patient = Patient.objects.filter(
            id=patient_id,
            is_active=True,
        ).first()

        if not patient:
            messages.error(request, "المريض غير موجود.")
            return redirect("inpatient:admission_create")

        # التحقق من الزيارة وأنها تخص المريض
        visit = None

        if visit_id:
            visit = Visit.objects.filter(
                id=visit_id,
                patient=patient,
            ).select_related(
                "department",
                "doctor",
            ).first()

            if not visit:
                messages.error(
                    request,
                    "الزيارة المحددة غير موجودة أو لا تخص هذا المريض.",
                )
                return redirect("inpatient:admission_create")

        department = None

        if department_id:
            department = Department.objects.filter(
                id=department_id,
                is_active=True,
            ).first()

            if not department:
                messages.error(request, "القسم المحدد غير موجود.")
                return redirect("inpatient:admission_create")

        doctor = None

        if doctor_id:
            doctor = Doctor.objects.filter(
                id=doctor_id,
                is_active=True,
            ).select_related("department").first()

            if not doctor:
                messages.error(request, "الطبيب المحدد غير موجود أو غير نشط.")
                return redirect("inpatient:admission_create")

        # إذا كانت الزيارة مرتبطة بقسم، نستخدم القسم المرتبط بها
        if visit and visit.department:
            if department and department.id != visit.department_id:
                messages.error(
                    request,
                    "القسم المحدد لا يطابق قسم الزيارة.",
                )
                return redirect("inpatient:admission_create")

            department = visit.department

        # إذا كانت الزيارة مرتبطة بطبيب، نستخدم الطبيب المرتبط بها
        if visit and visit.doctor:
            if doctor and doctor.id != visit.doctor_id:
                messages.error(
                    request,
                    "الطبيب المحدد لا يطابق طبيب الزيارة.",
                )
                return redirect("inpatient:admission_create")

            doctor = visit.doctor

        # التحقق من أن الطبيب تابع للقسم
        if doctor and department:
            if getattr(doctor, "department_id", None) != department.id:
                messages.error(
                    request,
                    "الطبيب المحدد لا يتبع للقسم المختار.",
                )
                return redirect("inpatient:admission_create")

        # التحقق من تاريخ الخروج المتوقع
        expected_discharge_date = None

        if expected_discharge_date_raw:
            try:
                expected_discharge_date = date.fromisoformat(
                    expected_discharge_date_raw
                )
            except ValueError:
                messages.error(
                    request,
                    "تاريخ الخروج المتوقع غير صحيح.",
                )
                return redirect("inpatient:admission_create")

        with transaction.atomic():
            # قفل السرير أثناء عملية الحجز لمنع حجزه من مستخدمين اثنين
            bed = (
                Bed.objects
                .select_for_update()
                .select_related("room", "room__department")
                .filter(
                    id=bed_id,
                    status="AVAILABLE",
                    room__is_active=True,
                )
                .first()
            )

            if not bed:
                messages.error(
                    request,
                    "السرير غير متاح حاليًا، ربما تم حجزه من مستخدم آخر.",
                )
                return redirect("inpatient:admission_create")

            # التحقق من توافق السرير مع القسم
            if department and bed.room.department_id:
                if bed.room.department_id != department.id:
                    messages.error(
                        request,
                        "السرير المحدد لا يتبع للقسم المختار.",
                    )
                    return redirect("inpatient:admission_create")

            # منع وجود تنويم نشط للمريض
            if Admission.objects.filter(
                patient=patient,
                status="ADMITTED",
            ).exists():
                messages.error(
                    request,
                    "المريض لديه حالة تنويم نشطة بالفعل.",
                )
                return redirect("inpatient:admission_create")

            admission = Admission.objects.create(
                admission_number=make_admission_number(),
                patient=patient,
                visit=visit,
                department=department,
                doctor=doctor,
                room=bed.room,
                bed=bed,
                admission_type=admission_type,
                status="ADMITTED",
                admission_diagnosis=diagnosis,
                clinical_notes=clinical_notes,
                expected_discharge_date=expected_discharge_date,
                admitted_by=request.user,
            )

            # تحويل السرير إلى مشغول
            bed.status = "OCCUPIED"
            bed.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            # تحويل الزيارة إلى قيد التنفيذ
            if visit:
                visit.status = "IN_PROGRESS"
                visit.save(
                    update_fields=[
                        "status",
                        "updated_at",
                    ]
                )

        messages.success(
            request,
            f"تم تنويم المريض بنجاح. رقم التنويم: {admission.admission_number}",
        )

        return redirect(
            "inpatient:admission_detail",
            admission_id=admission.id,
        )

    return render(
        request,
        "inpatient/admission_form.html",
        {
            "patients": patients,
            "departments": departments,
            "doctors": doctors,
            "beds": beds,
        },
    )


@login_required
def admission_detail(request, admission_id):
    admission = get_object_or_404(
        Admission.objects.select_related(
            "patient",
            "visit",
            "department",
            "doctor",
            "room",
            "bed",
            "admitted_by",
            "discharged_by",
        ),
        id=admission_id,
    )

    notes = admission.notes.select_related("author").all()
    vital_signs = admission.vital_signs.select_related(
        "recorded_by"
    ).all()

    transfers = admission.bed_transfers.select_related(
        "from_room",
        "from_bed",
        "to_room",
        "to_bed",
        "transferred_by",
    ).all()

    # --------------------------------------------------------
    # Laboratory orders linked to this inpatient admission
    # --------------------------------------------------------
    laboratory_orders = admission.laboratory_orders.select_related(
        "requesting_department",
        "requesting_doctor",
    ).prefetch_related(
        "items__test",
    ).order_by("-requested_at")

    # مدة الإقامة
    now = timezone.now()

    end_time = admission.discharged_at or now

    stay_duration = end_time - admission.admitted_at

    stay_days = stay_duration.days
    stay_hours = stay_duration.seconds // 3600

    # أنواع الخروج
    discharge_type_labels = {
        "HOME": "خروج إلى المنزل",
        "TRANSFER": "تحويل",
        "OBSERVATION": "تحت الملاحظة",
        "LEFT": "مغادرة بدون علاج",
        "OTHER": "أخرى",
    }

    discharge_type_label = discharge_type_labels.get(
        admission.discharge_type,
        admission.discharge_type or "-",
    )

    return render(
        request,
        "inpatient/admission_detail.html",
        {
            "admission": admission,
            "notes": notes,
            "vital_signs": vital_signs,
            "transfers": transfers,
            "laboratory_orders": laboratory_orders,
            "stay_days": stay_days,
            "stay_hours": stay_hours,
            "discharge_type_label": discharge_type_label,
        },
    )


@login_required
def admission_transfer(request, admission_id):
    admission = get_object_or_404(
        Admission.objects.select_related(
            "room",
            "bed",
        ),
        id=admission_id,
    )

    if admission.status != "ADMITTED":
        messages.error(
            request,
            "لا يمكن نقل مريض غير منوم حاليًا.",
        )
        return redirect(
            "inpatient:admission_detail",
            admission_id=admission.id,
        )

    beds = Bed.objects.filter(
        status="AVAILABLE",
        room__is_active=True,
    ).select_related("room")

    if request.method == "POST":
        new_bed_id = request.POST.get("bed")
        reason = request.POST.get("reason", "").strip()

        new_bed = beds.filter(id=new_bed_id).first()

        if not new_bed:
            messages.error(request, "السرير الجديد غير متاح.")
            return redirect(
                "inpatient:admission_transfer",
                admission_id=admission.id,
            )

        old_room = admission.room
        old_bed = admission.bed

        BedTransfer.objects.create(
            admission=admission,
            from_room=old_room,
            from_bed=old_bed,
            to_room=new_bed.room,
            to_bed=new_bed,
            reason=reason,
            transferred_by=request.user,
        )

        if old_bed:
            old_bed.status = "AVAILABLE"
            old_bed.save(update_fields=["status", "updated_at"])

        new_bed.status = "OCCUPIED"
        new_bed.save(update_fields=["status", "updated_at"])

        admission.room = new_bed.room
        admission.bed = new_bed
        admission.save(update_fields=["room", "bed", "updated_at"])

        messages.success(
            request,
            "تم نقل المريض إلى السرير الجديد بنجاح.",
        )

        return redirect(
            "inpatient:admission_detail",
            admission_id=admission.id,
        )

    return render(
        request,
        "inpatient/transfer_form.html",
        {
            "admission": admission,
            "beds": beds,
        },
    )


@login_required
def admission_discharge(request, admission_id):
    """
    إخراج المريض من التنويم بشكل آمن.
    جميع عمليات الخروج وتحرير السرير وتحديث الزيارة
    تتم داخل معاملة واحدة.
    """

    admission = get_object_or_404(
        Admission.objects.select_related(
            "patient",
            "bed",
            "room",
            "visit",
            "department",
            "doctor",
        ),
        id=admission_id,
    )

    if admission.status != "ADMITTED":
        messages.error(
            request,
            "هذه الحالة ليست تنويمًا نشطًا.",
        )
        return redirect(
            "inpatient:admission_detail",
            admission_id=admission.id,
        )

    if request.method == "POST":

        discharge_diagnosis = request.POST.get(
            "discharge_diagnosis",
            "",
        ).strip()

        discharge_notes = request.POST.get(
            "discharge_notes",
            "",
        ).strip()

        discharge_type = request.POST.get(
            "discharge_type",
            "HOME",
        ).strip()

        allowed_discharge_types = {
            "HOME",
            "TRANSFER",
            "OBSERVATION",
            "LEFT",
            "OTHER",
        }

        if discharge_type not in allowed_discharge_types:
            messages.error(
                request,
                "نوع الخروج غير صحيح.",
            )
            return redirect(
                "inpatient:admission_discharge",
                admission_id=admission.id,
            )

        if not discharge_diagnosis:
            messages.error(
                request,
                "يجب إدخال تشخيص الخروج.",
            )
            return redirect(
                "inpatient:admission_discharge",
                admission_id=admission.id,
            )

        now = timezone.now()

        with transaction.atomic():

            # قفل سجل التنويم لمنع تنفيذ الخروج مرتين بالتزامن
            locked_admission = (
                Admission.objects
                .select_for_update()
                .select_related(
                    "patient",
                    "visit",
                )
                .filter(
                    id=admission.id,
                    status="ADMITTED",
                )
                .first()
            )

            if not locked_admission:
                messages.error(
                    request,
                    "تم تغيير حالة التنويم بالفعل، ولا يمكن تنفيذ الخروج مرة أخرى.",
                )
                return redirect(
                    "inpatient:admission_detail",
                    admission_id=admission.id,
                )

            # قفل السرير قبل تحريره
            bed = None

            if locked_admission.bed_id:
                bed = (
                    Bed.objects
                    .select_for_update()
                    .filter(
                        id=locked_admission.bed_id,
                    )
                    .first()
                )

            # تغيير حالة التنويم
            locked_admission.status = "DISCHARGED"
            locked_admission.discharged_at = now
            locked_admission.discharge_diagnosis = discharge_diagnosis
            locked_admission.discharge_notes = discharge_notes
            locked_admission.discharge_type = discharge_type
            locked_admission.discharged_by = request.user

            locked_admission.save(
                update_fields=[
                    "status",
                    "discharged_at",
                    "discharge_diagnosis",
                    "discharge_notes",
                    "discharge_type",
                    "discharged_by",
                    "updated_at",
                ]
            )

            # تحرير السرير
            if bed:
                bed.status = "AVAILABLE"
                bed.save(
                    update_fields=[
                        "status",
                        "updated_at",
                    ]
                )

            # إكمال الزيارة المرتبطة بالتنويم
            if locked_admission.visit_id:
                visit = (
                    Visit.objects
                    .select_for_update()
                    .filter(id=locked_admission.visit_id)
                    .first()
                )

                if visit and visit.status != "CANCELLED":
                    visit.status = "COMPLETED"
                    visit.save(
                        update_fields=[
                            "status",
                            "updated_at",
                        ]
                    )

        messages.success(
            request,
            (
                f"تم خروج المريض "
                f"{locked_admission.patient.full_name} "
                f"من التنويم بنجاح. "
                f"رقم التنويم: {locked_admission.admission_number}"
            ),
        )

        return redirect(
            "inpatient:admission_detail",
            admission_id=locked_admission.id,
        )

    return render(
        request,
        "inpatient/discharge_form.html",
        {
            "admission": admission,
        },
    )


@login_required
def inpatient_note_create(request, admission_id):
    admission = get_object_or_404(
        Admission,
        id=admission_id,
    )

    if request.method == "POST":
        note_type = request.POST.get(
            "note_type",
            "PROGRESS",
        )

        note = request.POST.get(
            "note",
            "",
        ).strip()

        if not note:
            messages.error(
                request,
                "يرجى كتابة الملاحظة.",
            )
        else:
            InpatientNote.objects.create(
                admission=admission,
                note_type=note_type,
                note=note,
                author=request.user,
            )

            messages.success(
                request,
                "تم حفظ الملاحظة بنجاح.",
            )

    return redirect(
        "inpatient:admission_detail",
        admission_id=admission.id,
    )


@login_required
def inpatient_vitals_create(request, admission_id):
    admission = get_object_or_404(
        Admission,
        id=admission_id,
    )

    if request.method == "POST":
        def decimal_value(name):
            value = request.POST.get(name, "").strip()

            if not value:
                return None

            try:
                return value
            except Exception:
                return None

        def integer_value(name):
            value = request.POST.get(name, "").strip()

            if not value:
                return None

            try:
                return int(value)
            except (TypeError, ValueError):
                return None

        InpatientVitalSign.objects.create(
            admission=admission,
            temperature=decimal_value("temperature"),
            pulse=integer_value("pulse"),
            respiratory_rate=integer_value(
                "respiratory_rate"
            ),
            systolic_bp=integer_value(
                "systolic_bp"
            ),
            diastolic_bp=integer_value(
                "diastolic_bp"
            ),
            oxygen_saturation=decimal_value(
                "oxygen_saturation"
            ),
            pain_score=integer_value("pain_score"),
            recorded_by=request.user,
        )

        messages.success(
            request,
            "تم تسجيل العلامات الحيوية بنجاح.",
        )

    return redirect(
        "inpatient:admission_detail",
        admission_id=admission.id,
    )


@login_required
def inpatient_search(request):
    query = request.GET.get(
        "q",
        "",
    ).strip()

    admissions = Admission.objects.select_related(
        "patient",
        "department",
        "doctor",
        "room",
        "bed",
    )

    if query:
        admissions = admissions.filter(
            patient__full_name__icontains=query
        ) | Admission.objects.filter(
            admission_number__icontains=query
        )

    return render(
        request,
        "inpatient/search.html",
        {
            "query": query,
            "admissions": admissions.distinct(),
        },
    )
