from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.permissions import get_user_role
from patients.models import Patient, Visit
from laboratory.models import LaboratoryOrder

from .models import (
    SurgeryType,
    SurgeryOrder,
    SurgeryProcedure,
    SurgeryTeamMember,
    SurgeryPostoperativeNote,
)
from .forms import (
    SurgeryTypeForm,
    SurgeryOrderForm,
    SurgeryProcedureForm,
    SurgeryTeamMemberForm,
    SurgeryPostoperativeNoteForm,
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

        "total_surgery_types": SurgeryType.objects.filter(
            is_active=True
        ).count(),

        "total_orders": SurgeryOrder.objects.count(),

        "requested_orders": SurgeryOrder.objects.filter(
            status="REQUESTED"
        ).count(),

        "scheduled_orders": SurgeryOrder.objects.filter(
            status="SCHEDULED"
        ).count(),

        "preparation_orders": SurgeryOrder.objects.filter(
            status="PREPARATION"
        ).count(),

        "in_progress_orders": SurgeryOrder.objects.filter(
            status="IN_PROGRESS"
        ).count(),

        "recovery_orders": SurgeryOrder.objects.filter(
            status="RECOVERY"
        ).count(),

        "completed_orders": SurgeryOrder.objects.filter(
            status="COMPLETED"
        ).count(),

        "cancelled_orders": SurgeryOrder.objects.filter(
            status="CANCELLED"
        ).count(),

        "today_orders": SurgeryOrder.objects.filter(
            created_at__date=today
        ).count(),

        "recent_orders": SurgeryOrder.objects.select_related(
            "patient",
            "surgery_type",
            "surgeon",
        )[:10],
    }

    return render(request, "surgery/dashboard.html", context)


@login_required
def order_list(request):
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    priority = request.GET.get("priority", "").strip()

    orders = SurgeryOrder.objects.select_related(
        "patient",
        "surgery_type",
        "surgeon",
    )

    if q:
        orders = orders.filter(
            Q(order_number__icontains=q)
            | Q(patient__full_name__icontains=q)
            | Q(patient__patient_number__icontains=q)
            | Q(surgery_type__name_ar__icontains=q)
            | Q(surgery_type__name_en__icontains=q)
        )

    if status:
        orders = orders.filter(status=status)

    if priority:
        orders = orders.filter(priority=priority)

    context = {
        "orders": orders,
        "q": q,
        "status": status,
        "priority": priority,
        "status_choices": SurgeryOrder.STATUS_CHOICES,
        "priority_choices": SurgeryOrder.PRIORITY_CHOICES,
    }

    return render(request, "surgery/order_list.html", context)


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(
        SurgeryOrder.objects.select_related(
            "patient",
            "visit",
            "surgery_type",
            "surgeon",
            "requested_by",
        ),
        id=order_id,
    )

    procedures = order.procedures.select_related("surgeon").all()
    team_members = order.team_members.select_related("user").all()
    postoperative_notes = order.postoperative_notes.select_related(
        "recorded_by"
    ).all()

    context = {
        "order": order,
        "procedures": procedures,
        "team_members": team_members,
        "postoperative_notes": postoperative_notes,
    }

    return render(request, "surgery/order_detail.html", context)


@login_required
def order_create(request):
    if request.method == "POST":
        form = SurgeryOrderForm(request.POST)

        if form.is_valid():
            order = form.save(commit=False)
            order.requested_by = request.user
            order.save()

            messages.success(
                request,
                f"تم إنشاء طلب العملية {order.order_number} بنجاح."
            )

            return redirect(
                "surgery:order_detail",
                order_id=order.id,
            )
    else:
        form = SurgeryOrderForm()

    return render(
        request,
        "surgery/order_form.html",
        {
            "form": form,
            "title": "إنشاء طلب عملية",
        },
    )


@login_required
def order_update(request, order_id):
    order = get_object_or_404(SurgeryOrder, id=order_id)

    if request.method == "POST":
        form = SurgeryOrderForm(request.POST, instance=order)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "تم تحديث طلب العملية بنجاح."
            )

            return redirect(
                "surgery:order_detail",
                order_id=order.id,
            )
    else:
        form = SurgeryOrderForm(instance=order)

    return render(
        request,
        "surgery/order_form.html",
        {
            "form": form,
            "title": f"تعديل طلب العملية {order.order_number}",
            "order": order,
        },
    )


@login_required
def order_status_update(request, order_id, status):
    order = get_object_or_404(SurgeryOrder, id=order_id)

    allowed_statuses = {
        "REQUESTED",
        "SCHEDULED",
        "PREPARATION",
        "IN_PROGRESS",
        "RECOVERY",
        "COMPLETED",
        "CANCELLED",
    }

    if status not in allowed_statuses:
        messages.error(request, "حالة العملية غير صحيحة.")
        return redirect(
            "surgery:order_detail",
            order_id=order.id,
        )

    now = timezone.now()

    order.status = status

    if status == "SCHEDULED" and not order.scheduled_at:
        order.scheduled_at = now

    elif status == "IN_PROGRESS":
        if not order.started_at:
            order.started_at = now

    elif status == "COMPLETED":
        if not order.started_at:
            order.started_at = now

        if not order.completed_at:
            order.completed_at = now

    order.save(
        update_fields=[
            "status",
            "scheduled_at",
            "started_at",
            "completed_at",
            "updated_at",
        ]
    )

    messages.success(
        request,
        f"تم تغيير حالة العملية إلى: {order.get_status_display()}."
    )

    return redirect(
        "surgery:order_detail",
        order_id=order.id,
    )


@login_required
def procedure_create(request, order_id):
    order = get_object_or_404(SurgeryOrder, id=order_id)

    if request.method == "POST":
        form = SurgeryProcedureForm(request.POST)

        if form.is_valid():
            procedure = form.save(commit=False)
            procedure.order = order
            procedure.save()

            messages.success(
                request,
                "تمت إضافة الإجراء الجراحي بنجاح."
            )

            return redirect(
                "surgery:order_detail",
                order_id=order.id,
            )
    else:
        form = SurgeryProcedureForm(
            initial={
                "order": order.id,
                "surgeon": order.surgeon_id,
            }
        )

    return render(
        request,
        "surgery/procedure_form.html",
        {
            "form": form,
            "order": order,
        },
    )


@login_required
def team_member_create(request, order_id):
    order = get_object_or_404(SurgeryOrder, id=order_id)

    if request.method == "POST":
        form = SurgeryTeamMemberForm(request.POST)

        if form.is_valid():
            member = form.save(commit=False)
            member.order = order
            member.save()

            messages.success(
                request,
                "تمت إضافة عضو فريق العملية."
            )

            return redirect(
                "surgery:order_detail",
                order_id=order.id,
            )
    else:
        form = SurgeryTeamMemberForm(
            initial={
                "order": order.id,
            }
        )

    return render(
        request,
        "surgery/team_member_form.html",
        {
            "form": form,
            "order": order,
        },
    )


@login_required
def postoperative_note_create(request, order_id):
    order = get_object_or_404(SurgeryOrder, id=order_id)

    if request.method == "POST":
        form = SurgeryPostoperativeNoteForm(request.POST)

        if form.is_valid():
            note = form.save(commit=False)
            note.order = order
            note.recorded_by = request.user
            note.save()

            messages.success(
                request,
                "تمت إضافة ملاحظة ما بعد العملية."
            )

            return redirect(
                "surgery:order_detail",
                order_id=order.id,
            )
    else:
        form = SurgeryPostoperativeNoteForm(
            initial={
                "order": order.id,
            }
        )

    return render(
        request,
        "surgery/postoperative_note_form.html",
        {
            "form": form,
            "order": order,
        },
    )


@login_required
def surgery_type_list(request):
    types = SurgeryType.objects.all()

    q = request.GET.get("q", "").strip()

    if q:
        types = types.filter(
            Q(name_ar__icontains=q)
            | Q(name_en__icontains=q)
            | Q(code__icontains=q)
        )

    return render(
        request,
        "surgery/type_list.html",
        {
            "types": types,
            "q": q,
        },
    )


@login_required
def surgery_type_create(request):
    if request.method == "POST":
        form = SurgeryTypeForm(request.POST)

        if form.is_valid():
            surgery_type = form.save()

            messages.success(
                request,
                f"تم إنشاء نوع العملية: {surgery_type.name_ar}"
            )

            return redirect("surgery:type_list")
    else:
        form = SurgeryTypeForm()

    return render(
        request,
        "surgery/type_form.html",
        {
            "form": form,
            "title": "إضافة نوع عملية",
        },
    )


@login_required
def surgery_type_update(request, type_id):
    surgery_type = get_object_or_404(SurgeryType, id=type_id)

    if request.method == "POST":
        form = SurgeryTypeForm(
            request.POST,
            instance=surgery_type,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "تم تحديث نوع العملية."
            )

            return redirect("surgery:type_list")
    else:
        form = SurgeryTypeForm(instance=surgery_type)

    return render(
        request,
        "surgery/type_form.html",
        {
            "form": form,
            "title": "تعديل نوع عملية",
            "surgery_type": surgery_type,
        },
    )


@login_required
def patient_surgeries(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)

    orders = SurgeryOrder.objects.filter(
        patient=patient
    ).select_related(
        "surgery_type",
        "surgeon",
    )

    return render(
        request,
        "surgery/patient_surgeries.html",
        {
            "patient": patient,
            "orders": orders,
        },
    )
