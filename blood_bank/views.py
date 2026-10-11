from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from patients.models import Patient

from .forms import (
    BloodDonorForm,
    BloodUnitForm,
    BloodRequestForm,
    BloodIssueForm,
        BloodTransfusionForm,
    BloodCrossmatchForm,
)

from .models import (
    BloodDonor,
    BloodUnit,
    BloodRequest,
    BloodIssue,
        BloodTransfusion,
    BloodBankMovement,
    BloodCrossmatch,
)


@login_required
def dashboard(request):
    today = timezone.localdate()

    total_donors = BloodDonor.objects.filter(is_active=True).count()

    total_units = BloodUnit.objects.count()

    available_units = BloodUnit.objects.filter(
        status="AVAILABLE"
    ).count()

    reserved_units = BloodUnit.objects.filter(
        status="RESERVED"
    ).count()

    issued_units = BloodUnit.objects.filter(
        status="ISSUED"
    ).count()

    expired_units = BloodUnit.objects.filter(
        status="EXPIRED"
    ).count()

    pending_requests = BloodRequest.objects.filter(
        status__in=["REQUESTED", "CROSSMATCH"]
    ).count()

    today_requests = BloodRequest.objects.filter(
        created_at__date=today
    ).count()

    today_issues = BloodIssue.objects.filter(
        issued_at__date=today
    ).count()

    recent_requests = (
        BloodRequest.objects
        .select_related(
            "patient",
            "requesting_doctor",
            "requesting_department",
        )
        .order_by("-created_at")[:10]
    )

    blood_groups = []

    for group_code, group_name in BloodDonor.BLOOD_GROUPS:
        count = BloodUnit.objects.filter(
            blood_group=group_code,
            status="AVAILABLE",
        ).count()

        blood_groups.append({
            "code": group_code,
            "name": group_name,
            "count": count,
        })

    context = {
        "today": today,
        "total_donors": total_donors,
        "total_units": total_units,
        "available_units": available_units,
        "reserved_units": reserved_units,
        "issued_units": issued_units,
        "expired_units": expired_units,
        "pending_requests": pending_requests,
        "today_requests": today_requests,
        "today_issues": today_issues,
        "recent_requests": recent_requests,
        "blood_groups": blood_groups,
    }

    return render(
        request,
        "blood_bank/dashboard.html",
        context,
    )


@login_required
def donor_list(request):
    q = request.GET.get("q", "").strip()
    blood_group = request.GET.get("blood_group", "").strip()

    donors = BloodDonor.objects.all()

    if q:
        donors = donors.filter(
            Q(donor_number__icontains=q)
            | Q(full_name__icontains=q)
            | Q(phone__icontains=q)
            | Q(national_id__icontains=q)
        )

    if blood_group:
        donors = donors.filter(
            blood_group=blood_group
        )

    context = {
        "donors": donors,
        "q": q,
        "blood_group": blood_group,
        "blood_groups": BloodDonor.BLOOD_GROUPS,
    }

    return render(
        request,
        "blood_bank/donor_list.html",
        context,
    )


@login_required
def donor_create(request):
    if request.method == "POST":
        form = BloodDonorForm(request.POST)

        if form.is_valid():
            donor = form.save()

            messages.success(
                request,
                f"تمت إضافة المتبرع {donor.full_name} بنجاح.",
            )

            return redirect(
                "blood_bank:donor_list"
            )
    else:
        form = BloodDonorForm()

    return render(
        request,
        "blood_bank/donor_form.html",
        {
            "form": form,
            "title": "إضافة متبرع",
        },
    )


@login_required
def donor_update(request, donor_id):
    donor = get_object_or_404(
        BloodDonor,
        id=donor_id,
    )

    if request.method == "POST":
        form = BloodDonorForm(
            request.POST,
            instance=donor,
        )

        if form.is_valid():
            donor = form.save()

            messages.success(
                request,
                f"تم تحديث بيانات المتبرع {donor.full_name}.",
            )

            return redirect(
                "blood_bank:donor_list"
            )
    else:
        form = BloodDonorForm(
            instance=donor
        )

    return render(
        request,
        "blood_bank/donor_form.html",
        {
            "form": form,
            "donor": donor,
            "title": "تعديل متبرع",
        },
    )


@login_required
def unit_list(request):
    q = request.GET.get("q", "").strip()
    blood_group = request.GET.get("blood_group", "").strip()
    component = request.GET.get("component", "").strip()
    status = request.GET.get("status", "").strip()

    units = BloodUnit.objects.select_related(
        "donor"
    )

    if q:
        units = units.filter(
            Q(unit_number__icontains=q)
            | Q(donor__full_name__icontains=q)
            | Q(donor__donor_number__icontains=q)
        )

    if blood_group:
        units = units.filter(
            blood_group=blood_group
        )

    if component:
        units = units.filter(
            component=component
        )

    if status:
        units = units.filter(
            status=status
        )

    context = {
        "units": units,
        "q": q,
        "blood_group": blood_group,
        "component": component,
        "status": status,
        "blood_groups": BloodDonor.BLOOD_GROUPS,
        "component_choices": BloodUnit.COMPONENT_CHOICES,
        "status_choices": BloodUnit.STATUS_CHOICES,
    }

    return render(
        request,
        "blood_bank/unit_list.html",
        context,
    )


@login_required
def unit_create(request):
    if request.method == "POST":
        form = BloodUnitForm(request.POST)

        if form.is_valid():
            unit = form.save()

            BloodBankMovement.objects.create(
                blood_unit=unit,
                movement_type="RECEIVED",
                to_location=unit.storage_location,
                reference=unit.unit_number,
                notes="إضافة وحدة دم إلى بنك الدم",
                created_by=request.user,
            )

            messages.success(
                request,
                f"تمت إضافة وحدة الدم {unit.unit_number}.",
            )

            return redirect(
                "blood_bank:unit_list"
            )
    else:
        form = BloodUnitForm()

    return render(
        request,
        "blood_bank/unit_form.html",
        {
            "form": form,
            "title": "إضافة وحدة دم",
        },
    )


@login_required
def request_list(request):
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    priority = request.GET.get("priority", "").strip()

    requests = BloodRequest.objects.select_related(
        "patient",
        "requesting_doctor",
        "requesting_department",
    )

    if q:
        requests = requests.filter(
            Q(request_number__icontains=q)
            | Q(patient__full_name__icontains=q)
            | Q(patient__patient_number__icontains=q)
        )

    if status:
        requests = requests.filter(
            status=status
        )

    if priority:
        requests = requests.filter(
            priority=priority
        )

    context = {
        "blood_requests": requests,
        "q": q,
        "status": status,
        "priority": priority,
        "status_choices": BloodRequest.STATUS_CHOICES,
        "priority_choices": BloodRequest.PRIORITY_CHOICES,
    }

    return render(
        request,
        "blood_bank/request_list.html",
        context,
    )


@login_required
def request_create(request):
    if request.method == "POST":
        form = BloodRequestForm(request.POST)

        if form.is_valid():
            blood_request = form.save(
                commit=False
            )

            blood_request.requested_by = request.user
            blood_request.status = "REQUESTED"

            blood_request.save()

            messages.success(
                request,
                f"تم إنشاء طلب الدم {blood_request.request_number}.",
            )

            return redirect(
                "blood_bank:request_detail",
                request_id=blood_request.id,
            )
    else:
        form = BloodRequestForm()

    return render(
        request,
        "blood_bank/request_form.html",
        {
            "form": form,
            "title": "إنشاء طلب دم",
        },
    )


@login_required
def request_detail(request, request_id):
    blood_request = get_object_or_404(
        BloodRequest.objects.select_related(
            "patient",
            "visit",
            "requesting_doctor",
            "requesting_department",
            "requested_by",
        ),
        id=request_id,
    )

    issues = (
        BloodIssue.objects
        .filter(request=blood_request)
        .select_related(
            "blood_unit",
            "blood_unit__donor",
            "issued_by",
        )
        .prefetch_related(
            "transfusion",
        )
        .order_by("-issued_at")
    )

    crossmatches = (
        BloodCrossmatch.objects
        .filter(request=blood_request)
        .select_related(
            "blood_unit",
            "blood_unit__donor",
            "tested_by",
        )
        .order_by("-tested_at", "-id")
    )

    available_units = (
        BloodUnit.objects
        .filter(
            status="AVAILABLE",
            component=blood_request.component,
        )
        .select_related("donor")
        .order_by(
            "expiry_date",
            "unit_number",
        )
    )

    issue_form = BloodIssueForm()

    compatible_unit_ids = set(
        crossmatches
        .filter(result="COMPATIBLE")
        .values_list("blood_unit_id", flat=True)
    )

    compatible_crossmatch_count = crossmatches.filter(
        result="COMPATIBLE"
    ).count()

    pending_crossmatch_count = crossmatches.filter(
        result="PENDING"
    ).count()

    incompatible_crossmatch_count = crossmatches.filter(
        result="INCOMPATIBLE"
    ).count()

    context = {
        "blood_request": blood_request,
        "issues": issues,
        "crossmatches": crossmatches,
        "available_units": available_units,
        "issue_form": issue_form,
        "compatible_unit_ids": compatible_unit_ids,
        "compatible_crossmatch_count": compatible_crossmatch_count,
        "pending_crossmatch_count": pending_crossmatch_count,
        "incompatible_crossmatch_count": incompatible_crossmatch_count,
    }

    return render(
        request,
        "blood_bank/request_detail.html",
        context,
    )


@login_required
@transaction.atomic
def issue_blood(request, request_id):
    if request.method != "POST":
        return redirect(
            "blood_bank:request_detail",
            request_id=request_id,
        )

    blood_request = get_object_or_404(
        BloodRequest.objects.select_for_update(),
        id=request_id,
    )

    if blood_request.status in [
        "COMPLETED",
        "CANCELLED",
    ]:
        messages.error(
            request,
            "لا يمكن صرف الدم لهذا الطلب.",
        )

        return redirect(
            "blood_bank:request_detail",
            request_id=blood_request.id,
        )

    form = BloodIssueForm(request.POST)

    if not form.is_valid():
        messages.error(
            request,
            "يرجى اختيار وحدة دم صحيحة.",
        )

        return redirect(
            "blood_bank:request_detail",
            request_id=blood_request.id,
        )

    unit_id = form.cleaned_data["blood_unit"].id

    unit = get_object_or_404(
        BloodUnit.objects.select_for_update(),
        id=unit_id,
    )

    if unit.status != "AVAILABLE":
        messages.error(
            request,
            f"وحدة الدم {unit.unit_number} لم تعد متاحة.",
        )

        return redirect(
            "blood_bank:request_detail",
            request_id=blood_request.id,
        )

    today = timezone.localdate()

    if unit.expiry_date < today:
        unit.status = "EXPIRED"
        unit.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        BloodBankMovement.objects.create(
            blood_unit=unit,
            movement_type="EXPIRED",
            reference=unit.unit_number,
            notes="تم اكتشاف انتهاء صلاحية الوحدة أثناء محاولة الصرف",
            created_by=request.user,
        )

        messages.error(
            request,
            f"وحدة الدم {unit.unit_number} منتهية الصلاحية.",
        )

        return redirect(
            "blood_bank:request_detail",
            request_id=blood_request.id,
        )

    # ---------------------------------------------------------
    # شروط السلامة قبل صرف وحدة الدم
    # ---------------------------------------------------------

    # يجب أن تكون نتيجة فحص الوحدة سلبية قبل صرفها.
    if unit.screening_result != "NEGATIVE":
        messages.error(
            request,
            f"لا يمكن صرف الوحدة {unit.unit_number}: "
            "نتيجة الفحص المخبري للوحدة ليست NEGATIVE.",
        )

        return redirect(
            "blood_bank:request_detail",
            request_id=blood_request.id,
        )

    # يجب أن تتطابق فصيلة الوحدة مع فصيلة المتبرع المسجلة.
    if unit.blood_group != unit.donor.blood_group:
        messages.error(
            request,
            f"لا يمكن صرف الوحدة {unit.unit_number}: "
            "فصيلة الوحدة لا تطابق فصيلة المتبرع.",
        )

        return redirect(
            "blood_bank:request_detail",
            request_id=blood_request.id,
        )

    # يجب وجود Crossmatch متوافق لنفس الطلب ونفس الوحدة.
    compatible_crossmatch = BloodCrossmatch.objects.filter(
        request=blood_request,
        blood_unit=unit,
        result="COMPATIBLE",
    ).order_by("-tested_at", "-id").first()

    if compatible_crossmatch is None:
        messages.error(
            request,
            f"لا يمكن صرف الوحدة {unit.unit_number}: "
            "لا يوجد اختبار Crossmatch متوافق لهذه الوحدة مع هذا الطلب.",
        )

        return redirect(
            "blood_bank:request_detail",
            request_id=blood_request.id,
        )

    # التأكد من أن الفصائل المسجلة في Crossmatch ما زالت مطابقة
    # للفصائل الحالية للطلب والوحدة.
    patient_blood_group = (
        blood_request.patient_blood_group
        or getattr(blood_request.patient, "blood_group", "")
    )

    if (
        compatible_crossmatch.patient_blood_group
        != patient_blood_group
        or compatible_crossmatch.unit_blood_group
        != unit.blood_group
    ):
        messages.error(
            request,
            "لا يمكن صرف الوحدة: بيانات اختبار Crossmatch لا تطابق "
            "بيانات المريض أو الوحدة الحالية.",
        )

        return redirect(
            "blood_bank:request_detail",
            request_id=blood_request.id,
        )

    issue = BloodIssue.objects.create(
        request=blood_request,
        blood_unit=unit,
        issued_by=request.user,
        notes=form.cleaned_data.get(
            "notes",
            "",
        ),
    )

    unit.status = "ISSUED"

    unit.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    BloodBankMovement.objects.create(
        blood_unit=unit,
        movement_type="ISSUED",
        from_location=unit.storage_location,
        reference=blood_request.request_number,
        notes="صرف وحدة دم لطلب مريض",
        created_by=request.user,
    )

    issued_count = blood_request.issues.count()

    if issued_count >= blood_request.units_requested:
        blood_request.status = "ISSUED"
    else:
        blood_request.status = "READY"

    blood_request.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    messages.success(
        request,
        f"تم صرف وحدة الدم {unit.unit_number} "
        f"للطلب {blood_request.request_number}.",
    )

    return redirect(
        "blood_bank:request_detail",
        request_id=blood_request.id,
    )


@login_required
@transaction.atomic
def start_transfusion(request, issue_id):
    if request.method != "POST":
        return redirect(
            "blood_bank:request_list"
        )

    issue = get_object_or_404(
        BloodIssue.objects.select_related(
            "request",
            "blood_unit",
        ),
        id=issue_id,
    )

    transfusion, created = (
        BloodTransfusion.objects.get_or_create(
            issue=issue,
            defaults={
                "patient": issue.request.patient,
                "status": "STARTED",
                "started_at": timezone.now(),
                "performed_by": request.user,
            },
        )
    )

    if not created:
        messages.warning(
            request,
            "تم تسجيل نقل الدم لهذه الوحدة مسبقًا.",
        )
    else:
        messages.success(
            request,
            "تم بدء تسجيل عملية نقل الدم.",
        )

    return redirect(
        "blood_bank:request_detail",
        request_id=issue.request.id,
    )


@login_required
@transaction.atomic
def update_transfusion(request, transfusion_id):
    transfusion = get_object_or_404(
        BloodTransfusion.objects.select_related(
            "issue",
            "patient",
        ),
        id=transfusion_id,
    )

    if request.method != "POST":
        return redirect(
            "blood_bank:request_detail",
            request_id=transfusion.issue.request.id,
        )

    form = BloodTransfusionForm(request.POST)

    if not form.is_valid():
        messages.error(
            request,
            "بيانات نقل الدم غير صحيحة.",
        )

        return redirect(
            "blood_bank:request_detail",
            request_id=transfusion.issue.request.id,
        )

    status = form.cleaned_data["status"]

    transfusion.status = status
    transfusion.reaction_notes = (
        form.cleaned_data["reaction_notes"]
    )
    transfusion.notes = (
        form.cleaned_data["notes"]
    )
    transfusion.performed_by = request.user

    if not transfusion.started_at:
        transfusion.started_at = timezone.now()

    if status in [
        "COMPLETED",
        "STOPPED",
        "REACTION",
    ]:
        transfusion.completed_at = timezone.now()

    transfusion.save()

    if status == "COMPLETED":
        unit = transfusion.issue.blood_unit

        unit.status = "TRANSFUSED"

        unit.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        BloodBankMovement.objects.create(
            blood_unit=unit,
            movement_type="ISSUED",
            reference=transfusion.issue.request.request_number,
            notes="اكتملت عملية نقل الدم",
            created_by=request.user,
        )

        blood_request = transfusion.issue.request

        blood_request.status = "COMPLETED"
        blood_request.completed_at = timezone.now()

        blood_request.save(
            update_fields=[
                "status",
                "completed_at",
                "updated_at",
            ]
        )

        messages.success(
            request,
            "تم إكمال عملية نقل الدم بنجاح.",
        )

    elif status == "REACTION":
        messages.warning(
            request,
            "تم تسجيل تفاعل أثناء نقل الدم. "
            "يرجى توثيق الحالة ومتابعتها طبيًا.",
        )

    elif status == "STOPPED":
        messages.warning(
            request,
            "تم تسجيل إيقاف عملية نقل الدم.",
        )

    else:
        messages.success(
            request,
            "تم تحديث حالة نقل الدم.",
        )

    return redirect(
        "blood_bank:request_detail",
        request_id=transfusion.issue.request.id,
    )


@login_required
def movement_list(request):
    q = request.GET.get("q", "").strip()
    movement_type = request.GET.get(
        "movement_type",
        "",
    ).strip()

    movements = BloodBankMovement.objects.select_related(
        "blood_unit",
        "created_by",
    )

    if q:
        movements = movements.filter(
            Q(blood_unit__unit_number__icontains=q)
            | Q(reference__icontains=q)
            | Q(blood_unit__donor__full_name__icontains=q)
        )

    if movement_type:
        movements = movements.filter(
            movement_type=movement_type
        )

    context = {
        "movements": movements[:300],
        "q": q,
        "movement_type": movement_type,
        "movement_choices": BloodBankMovement.MOVEMENT_CHOICES,
    }

    return render(
        request,
        "blood_bank/movement_list.html",
        context,
    )


@login_required
def patient_requests(request, patient_id):
    patient = get_object_or_404(
        Patient,
        id=patient_id,
    )

    blood_requests = (
        BloodRequest.objects
        .filter(patient=patient)
        .select_related(
            "requesting_doctor",
            "requesting_department",
        )
    )

    return render(
        request,
        "blood_bank/request_list.html",
        {
            "blood_requests": blood_requests,
            "patient": patient,
            "q": "",
            "status": "",
            "priority": "",
            "status_choices": BloodRequest.STATUS_CHOICES,
            "priority_choices": BloodRequest.PRIORITY_CHOICES,
        },
    )

@login_required
@transaction.atomic
def crossmatch_create(request, request_id):
    blood_request = get_object_or_404(
        BloodRequest.objects.select_related(
            "patient",
            "requesting_doctor",
            "requesting_department",
        ),
        pk=request_id,
    )

    if blood_request.status in ["COMPLETED", "CANCELLED"]:
        messages.error(
            request,
            "لا يمكن إجراء اختبار توافق لطلب مكتمل أو ملغى."
        )
        return redirect(
            "blood_bank:request_detail",
            request_id=blood_request.id,
        )

    if request.method == "POST":
        form = BloodCrossmatchForm(
            request.POST,
            blood_request=blood_request,
        )

        if form.is_valid():
            blood_unit = form.cleaned_data["blood_unit"]

            blood_unit = (
                BloodUnit.objects
                .select_for_update()
                .select_related("donor")
                .get(pk=blood_unit.pk)
            )

            patient_blood_group = (
                blood_request.patient_blood_group
                or getattr(
                    blood_request.patient,
                    "blood_group",
                    ""
                )
            )

            if not patient_blood_group:
                messages.error(
                    request,
                    "فصيلة دم المريض غير محددة. يجب تحديدها قبل إجراء اختبار التوافق."
                )
                return redirect(
                    "blood_bank:request_detail",
                    request_id=blood_request.id,
                )

            if blood_unit.status != "AVAILABLE":
                messages.error(
                    request,
                    "وحدة الدم المختارة لم تعد متاحة."
                )
                return redirect(
                    "blood_bank:crossmatch_create",
                    request_id=blood_request.id,
                )

            if blood_unit.expiry_date < timezone.localdate():
                blood_unit.status = "EXPIRED"
                blood_unit.save(update_fields=["status", "updated_at"])

                messages.error(
                    request,
                    "وحدة الدم منتهية الصلاحية."
                )
                return redirect(
                    "blood_bank:crossmatch_create",
                    request_id=blood_request.id,
                )

            if blood_unit.screening_result != "NEGATIVE":
                messages.error(
                    request,
                    "لا يمكن إجراء اختبار توافق لوحدة لم تجتز فحص العدوى/الفحص المخبري."
                )
                return redirect(
                    "blood_bank:crossmatch_create",
                    request_id=blood_request.id,
                )

            if blood_unit.blood_group != blood_unit.donor.blood_group:
                messages.error(
                    request,
                    "فصيلة وحدة الدم لا تطابق فصيلة المتبرع المسجلة."
                )
                return redirect(
                    "blood_bank:crossmatch_create",
                    request_id=blood_request.id,
                )

            result = form.cleaned_data["result"]

            if result == "COMPATIBLE":
                if blood_unit.blood_group != patient_blood_group:
                    messages.error(
                        request,
                        "لا يمكن تسجيل Compatible لأن فصيلة وحدة الدم لا تطابق فصيلة المريض."
                    )
                    return redirect(
                        "blood_bank:crossmatch_create",
                        request_id=blood_request.id,
                    )

            crossmatch = form.save(commit=False)
            crossmatch.request = blood_request
            crossmatch.patient_blood_group = patient_blood_group
            crossmatch.unit_blood_group = blood_unit.blood_group
            crossmatch.tested_by = request.user
            crossmatch.tested_at = timezone.now()
            crossmatch.save()

            if result == "COMPATIBLE":
                blood_request.status = "READY"
                blood_request.save(
                    update_fields=["status", "updated_at"]
                )
                messages.success(
                    request,
                    f"تم تسجيل اختبار توافق ناجح للوحدة {blood_unit.unit_number}."
                )
            elif result == "INCOMPATIBLE":
                messages.warning(
                    request,
                    f"تم تسجيل عدم توافق الوحدة {blood_unit.unit_number}."
                )
            elif result == "CANCELLED":
                messages.warning(
                    request,
                    "تم إلغاء اختبار التوافق."
                )
            else:
                messages.info(
                    request,
                    "تم تسجيل اختبار التوافق بحالة Pending."
                )

            return redirect(
                "blood_bank:request_detail",
                request_id=blood_request.id,
            )

    else:
        form = BloodCrossmatchForm(
            blood_request=blood_request,
        )

    crossmatches = (
        BloodCrossmatch.objects
        .filter(request=blood_request)
        .select_related(
            "blood_unit",
            "tested_by",
        )
    )

    return render(
        request,
        "blood_bank/crossmatch_form.html",
        {
            "form": form,
            "blood_request": blood_request,
            "crossmatches": crossmatches,
        },
    )