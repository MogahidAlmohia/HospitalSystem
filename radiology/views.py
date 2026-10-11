from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.contrib import messages

from accounts.permissions import get_user_role
from patients.models import Patient, Visit
from doctors.models import Doctor
from departments.models import Department

from .models import RadiologyExamType, RadiologyOrder
from .forms import (
    RadiologyOrderForm,
    RadiologyReportForm,
    RadiologyExamTypeForm,
)


def _generate_order_number():
    today = timezone.localdate().strftime("%Y%m%d")
    prefix = f"RAD-{today}-"

    last = (
        RadiologyOrder.objects
        .filter(order_number__startswith=prefix)
        .order_by("-id")
        .first()
    )

    if last:
        try:
            number = int(last.order_number.split("-")[-1]) + 1
        except (ValueError, IndexError):
            number = 1
    else:
        number = 1

    return f"{prefix}{number:04d}"


@login_required
def dashboard(request):
    role = get_user_role(request.user)
    today = timezone.localdate()

    orders = RadiologyOrder.objects.all()

    context = {
        "role": role,
        "today": today,
        "total_patients": Patient.objects.count(),
        "today_visits": Visit.objects.filter(
            created_at__date=today
        ).count(),

        "total_orders": orders.count(),

        "today_orders": orders.filter(
            created_at__date=today
        ).count(),

        "requested_orders": orders.filter(
            status="REQUESTED"
        ).count(),

        "scheduled_orders": orders.filter(
            status="SCHEDULED"
        ).count(),

        "in_progress_orders": orders.filter(
            status="IN_PROGRESS"
        ).count(),

        "completed_orders": orders.filter(
            status="COMPLETED"
        ).count(),

        "reported_orders": orders.filter(
            status="REPORTED"
        ).count(),

        "delivered_orders": orders.filter(
            status="DELIVERED"
        ).count(),

        "urgent_orders": orders.filter(
            priority__in=["URGENT", "STAT"]
        ).exclude(
            status__in=["DELIVERED", "CANCELLED"]
        ).count(),

        "recent_orders": orders.select_related(
            "patient",
            "exam_type",
            "requesting_doctor",
        )[:10],
    }

    return render(
        request,
        "radiology/dashboard.html",
        context
    )


@login_required
def order_list(request):
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    priority = request.GET.get("priority", "").strip()

    orders = RadiologyOrder.objects.select_related(
        "patient",
        "exam_type",
        "requesting_doctor",
        "requesting_department",
    )

    if q:
        orders = orders.filter(
            Q(order_number__icontains=q)
            | Q(patient__full_name__icontains=q)
            | Q(patient__patient_number__icontains=q)
            | Q(exam_type__name_ar__icontains=q)
            | Q(exam_type__name_en__icontains=q)
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
        "status_choices": RadiologyOrder.STATUS_CHOICES,
        "priority_choices": RadiologyOrder.PRIORITY_CHOICES,
    }

    return render(
        request,
        "radiology/order_list.html",
        context
    )


@login_required
def order_create(request):
    if request.method == "POST":
        form = RadiologyOrderForm(request.POST)

        if form.is_valid():
            order = form.save(commit=False)
            order.order_number = _generate_order_number()
            order.requested_by = request.user
            order.status = "REQUESTED"
            order.save()

            messages.success(
                request,
                f"تم إنشاء طلب الأشعة {order.order_number} بنجاح."
            )

            return redirect(
                "radiology:order_detail",
                order_id=order.id
            )
    else:
        form = RadiologyOrderForm()

    return render(
        request,
        "radiology/order_form.html",
        {
            "form": form,
            "title": "إنشاء طلب أشعة",
        }
    )


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(
        RadiologyOrder.objects.select_related(
            "patient",
            "visit",
            "requesting_doctor",
            "requesting_department",
            "exam_type",
            "reported_by",
            "requested_by",
        ),
        id=order_id,
    )

    return render(
        request,
        "radiology/order_detail.html",
        {"order": order}
    )


@login_required
def order_update_status(request, order_id):
    order = get_object_or_404(RadiologyOrder, id=order_id)

    if request.method == "POST":
        new_status = request.POST.get("status", "").strip()

        valid_statuses = dict(
            RadiologyOrder.STATUS_CHOICES
        )

        if new_status in valid_statuses:
            order.status = new_status

            if new_status == "IN_PROGRESS" and not order.performed_at:
                order.performed_at = timezone.now()

            if new_status == "DELIVERED":
                order.delivered_at = timezone.now()

            order.save()

            messages.success(
                request,
                "تم تحديث حالة طلب الأشعة."
            )

    return redirect(
        "radiology:order_detail",
        order_id=order.id
    )


@login_required
def report_create(request, order_id):
    order = get_object_or_404(
        RadiologyOrder,
        id=order_id
    )

    if request.method == "POST":
        form = RadiologyReportForm(
            request.POST,
            instance=order
        )

        if form.is_valid():
            order = form.save(commit=False)
            order.reported_by = request.user

            if order.status in [
                "REQUESTED",
                "SCHEDULED",
                "IN_PROGRESS",
                "COMPLETED",
            ]:
                order.status = "REPORTED"

            order.save()

            messages.success(
                request,
                "تم حفظ تقرير الأشعة بنجاح."
            )

            return redirect(
                "radiology:order_detail",
                order_id=order.id
            )
    else:
        form = RadiologyReportForm(
            instance=order
        )

    return render(
        request,
        "radiology/report_form.html",
        {
            "form": form,
            "order": order,
        }
    )


@login_required
def exam_type_list(request):
    exam_types = RadiologyExamType.objects.all()

    return render(
        request,
        "radiology/exam_type_list.html",
        {"exam_types": exam_types}
    )


@login_required
def exam_type_create(request):
    if request.method == "POST":
        form = RadiologyExamTypeForm(request.POST)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "تمت إضافة نوع فحص الأشعة."
            )

            return redirect(
                "radiology:exam_type_list"
            )
    else:
        form = RadiologyExamTypeForm()

    return render(
        request,
        "radiology/exam_type_form.html",
        {
            "form": form,
            "title": "إضافة نوع فحص أشعة",
        }
    )


@login_required
def patient_orders(request, patient_id):
    patient = get_object_or_404(
        Patient,
        id=patient_id
    )

    orders = RadiologyOrder.objects.filter(
        patient=patient
    ).select_related(
        "exam_type",
        "requesting_doctor",
    )

    return render(
        request,
        "radiology/patient_orders.html",
        {
            "patient": patient,
            "orders": orders,
        }
    )
