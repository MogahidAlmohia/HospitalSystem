from decimal import Decimal, InvalidOperation

from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from django.http import HttpResponse
from django.db import models
from decimal import Decimal, InvalidOperation
import re
import os
from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from reception.models import Visit
from inpatient.models import Admission
from departments.models import Department
from doctors.models import Doctor

from .models import (
    LaboratoryOrder,
    LaboratoryOrderItem,
    LaboratoryTest,
    LaboratoryReportSettings,
    LaboratoryResultDelivery,
    LaboratoryAuditLog,
)

from .department_access import (
    is_lab_manager,
    get_user_lab_department,
    is_central_laboratory_user,
    user_can_access_test,
    user_can_access_order,
    user_can_access_order_item,
    laboratory_department_filter,
)

from accounts.permissions import user_has_permission
from system_settings.services import get_hospital_identity


# ============================================================
# Laboratory Department Access Helpers
# ============================================================

def lab_access_denied(request, message="ليس لديك صلاحية للوصول إلى هذه البيانات."):
    messages.error(request, message)
    return redirect("laboratory:dashboard")


def lab_require_permission(request, permission, message="ليس لديك الصلاحية لتنفيذ هذه العملية."):
    """
    حماية مباشرة داخل View بالإضافة إلى حماية Middleware.
    """
    if not user_has_permission(request.user, permission):
        messages.error(request, message)
        return False
    return True


def get_lab_user_tests(user, queryset=None):
    """
    Return laboratory tests accessible to the current laboratory user.

    ADMIN / MANAGER:
        All tests.

    Central Laboratory:
        All tests.

    Other laboratory departments:
        Only tests assigned to their department.
    """
    if queryset is None:
        queryset = LaboratoryTest.objects.all()

    if is_lab_manager(user):
        return queryset

    department = get_user_lab_department(user)

    if not department:
        return queryset.none()

    if department.code == "LAB":
        return queryset

    return queryset.filter(department_id=department.id)




def get_lab_user_order_items(user, order):
    """
    إرجاع عناصر طلب المختبر المسموح للمستخدم برؤيتها.

    المدير:
        يرى جميع العناصر.

    المختبر المركزي LAB:
        يرى جميع العناصر.

    مستخدم قسم مختبر:
        يرى فقط العناصر التابعة لقسمه.

    هذه الدالة مهمة جدًا لمنع ظهور عناصر قسم آخر
    داخل طلب مختلط يحتوي على أكثر من قسم.
    """
    items = order.items.select_related(
        "test",
        "test__department",
        "examiner",
    )

    if is_lab_manager(user):
        return items

    department = get_user_lab_department(user)

    if not department:
        return items.none()

    if department.code == "LAB":
        return items

    return items.filter(
        test__department_id=department.id
    )

def get_lab_user_orders(user, queryset=None):
    """
    Return laboratory orders accessible to the current user.

    Central Laboratory and managers can access all orders.

    Department laboratory users can access orders containing
    at least one test belonging to their department.
    """
    if queryset is None:
        queryset = LaboratoryOrder.objects.all()

    if is_lab_manager(user):
        return queryset

    department = get_user_lab_department(user)

    if not department:
        return queryset.none()

    if department.code == "LAB":
        return queryset

    return queryset.filter(
        items__test__department_id=department.id
    ).distinct()


def get_lab_user_devices(user, queryset=None):
    """
    Return laboratory devices belonging to the user's department.
    """
    if queryset is None:
        from .models_inventory import LaboratoryDevice
        queryset = LaboratoryDevice.objects.all()

    if is_lab_manager(user):
        return queryset

    department = get_user_lab_department(user)

    if not department:
        return queryset.none()

    if department.code == "LAB":
        return queryset

    return queryset.filter(department_id=department.id)


# ============================================================
# Helper: Calculate H / L / NORMAL
# ============================================================

def calculate_result_flag(numeric_value, reference_range):
    """
    Calculates laboratory result flag.

    H      = High
    L      = Low
    NORMAL = Within reference range
    """

    if numeric_value is None or not reference_range:
        return ""

    try:
        value = float(numeric_value)
    except (ValueError, TypeError):
        return ""

    text = str(reference_range).strip()

    numbers = re.findall(
        r"-?\d+(?:\.\d+)?",
        text
    )

    if len(numbers) < 2:
        return ""

    try:
        low = float(numbers[0])
        high = float(numbers[1])
    except (ValueError, TypeError):
        return ""

    if value < low:
        return "L"

    if value > high:
        return "H"

    return "NORMAL"


def calculate_critical_status(numeric_value, test):
    """
    Detect Critical Laboratory Values.

    Returns:
        CRITICAL_LOW
        CRITICAL_HIGH
        ""
    """

    if numeric_value is None or test is None:
        return ""

    try:
        value = Decimal(str(numeric_value))
    except (InvalidOperation, ValueError, TypeError):
        return ""

    if test.critical_low is not None and value <= test.critical_low:
        return "CRITICAL_LOW"

    if test.critical_high is not None and value >= test.critical_high:
        return "CRITICAL_HIGH"

    return ""


# ============================================================
# Laboratory Dashboard
# ============================================================

@login_required
def laboratory_dashboard(request):
    """
    لوحة التحكم الرئيسية للمختبر.

    هذه الصفحة للعرض والإحصائيات والبحث فقط.
    لا تقوم بحذف أو تعديل أي بيانات في قاعدة البيانات.
    """

    from django.db.models import Count, Q, F

    # --------------------------------------------------------
    # جميع الطلبات
    # --------------------------------------------------------

    base_orders = LaboratoryOrder.objects.all()

    # --------------------------------------------------------
    # البحث
    # --------------------------------------------------------

    query = request.GET.get("q", "").strip()

    orders = (
        LaboratoryOrder.objects
        .select_related(
            "patient",
            "visit",
            "admission",
            "requesting_department",
            "requesting_doctor",
        )
        .prefetch_related(
            "items__test",
            "items__examiner",
        )
        .order_by("-requested_at", "-id")
    )

    if query:
        orders = orders.filter(
            Q(order_number__icontains=query)
            | Q(patient__full_name__icontains=query)
            | Q(patient__patient_number__icontains=query)
            | Q(requesting_doctor__full_name__icontains=query)
            | Q(requesting_department__name_ar__icontains=query)
            | Q(requesting_department__name_en__icontains=query)
        ).distinct()

    # --------------------------------------------------------
    # فلترة الحالة
    # --------------------------------------------------------

    status_filter = request.GET.get("status", "").strip()

    allowed_statuses = {
        "REQUESTED",
        "RECEIVED",
        "COLLECTED",
        "PROCESSING",
        "COMPLETED",
        "CANCELLED",
    }

    if status_filter in allowed_statuses:
        orders = orders.filter(status=status_filter)

    # --------------------------------------------------------
    # فلترة الأولوية
    # --------------------------------------------------------

    priority_filter = request.GET.get("priority", "").strip()

    allowed_priorities = {
        "NORMAL",
        "URGENT",
        "STAT",
    }

    if priority_filter in allowed_priorities:
        orders = orders.filter(priority=priority_filter)

    # --------------------------------------------------------
    # الإحصائيات الرئيسية
    # --------------------------------------------------------

    total_count = base_orders.count()

    requested_count = base_orders.filter(
        status="REQUESTED"
    ).count()

    received_count = base_orders.filter(
        status="RECEIVED"
    ).count()

    collected_count = base_orders.filter(
        status="COLLECTED"
    ).count()

    processing_count = base_orders.filter(
        status="PROCESSING"
    ).count()

    completed_count = base_orders.filter(
        status="COMPLETED"
    ).count()

    cancelled_count = base_orders.filter(
        status="CANCELLED"
    ).count()

    # --------------------------------------------------------
    # الأولويات
    # --------------------------------------------------------

    urgent_count = base_orders.filter(
        priority="URGENT"
    ).exclude(
        status__in=["COMPLETED", "CANCELLED"]
    ).count()

    stat_count = base_orders.filter(
        priority="STAT"
    ).exclude(
        status__in=["COMPLETED", "CANCELLED"]
    ).count()

    # --------------------------------------------------------
    # النتائج التي تحتاج اعتماد
    # --------------------------------------------------------

    verification_count = (
        base_orders
        .filter(status="PROCESSING")
        .annotate(
            total_items=Count(
                "items",
                filter=~Q(items__status="CANCELLED"),
                distinct=True,
            ),
            verified_items=Count(
                "items",
                filter=(
                    Q(items__verified=True)
                    & ~Q(items__status="CANCELLED")
                ),
                distinct=True,
            ),
        )
        .filter(
            total_items__gt=0,
            verified_items__lt=F("total_items"),
        )
        .count()
    )

    # --------------------------------------------------------
    # إحصائيات الأقسام
    # --------------------------------------------------------

    department_stats = (
        base_orders
        .values(
            "requesting_department__id",
            "requesting_department__name_ar",
        )
        .annotate(
            total=Count("id"),
            pending=Count(
                "id",
                filter=Q(
                    status__in=[
                        "REQUESTED",
                        "RECEIVED",
                        "COLLECTED",
                        "PROCESSING",
                    ]
                ),
            ),
            completed=Count(
                "id",
                filter=Q(status="COMPLETED"),
            ),
        )
        .order_by("-total")
    )

    # --------------------------------------------------------
    # آخر الطلبات
    # --------------------------------------------------------

    recent_orders = orders[:100]

    # --------------------------------------------------------
    # أسماء الحالات بالعربي
    # --------------------------------------------------------

    status_labels = {
        "REQUESTED": "طلب جديد",
        "RECEIVED": "تم الاستلام",
        "COLLECTED": "تم سحب العينة",
        "PROCESSING": "قيد المعالجة",
        "COMPLETED": "مكتمل",
        "CANCELLED": "ملغى",
    }

    priority_labels = {
        "NORMAL": "عادي",
        "URGENT": "عاجل",
        "STAT": "STAT",
    }

    # --------------------------------------------------------
    # إحصائيات إرسال واستلام النتائج
    # --------------------------------------------------------

    # الطلبات التي تم إرسال نتائجها
    sent_order_ids = set(
        LaboratoryResultDelivery.objects
        .filter(order_id__in=orders.values_list("id", flat=True))
        .values_list("order_id", flat=True)
    )

    sent_orders_count = len(sent_order_ids)

    # الطلبات التي تم استلام نتائجها من القسم/الطبيب
    received_order_ids = set(
        LaboratoryResultDelivery.objects
        .filter(
            order_id__in=orders.values_list("id", flat=True),
            received_at__isnull=False,
        )
        .values_list("order_id", flat=True)
    )

    received_orders_count = len(received_order_ids)

    # --------------------------------------------------------
    # فحص سلامة بيانات النتائج
    # --------------------------------------------------------

    integrity_problem_items = (
        LaboratoryOrderItem.objects
        .filter(
            order_id__in=orders.values_list("id", flat=True)
        )
        .exclude(status="CANCELLED")
        .filter(
            result_numeric__isnull=False
        )
        .filter(
            models.Q(result_flag__isnull=True)
            | models.Q(result_flag="")
        )
        .select_related("order", "test", "order__patient")
        .order_by("-updated_at")
    )

    integrity_problem_count = integrity_problem_items.count()

    # --------------------------------------------------------
    # Context
    # --------------------------------------------------------

    # عدد الطلبات الجاهزة لإصدار التقرير
    # Report Ready = جميع العناصر غير الملغاة تم التحقق منها
    report_ready_count = 0

    for dashboard_order in orders:
        active_items = dashboard_order.items.exclude(
            status="CANCELLED"
        )

        if (
            active_items.exists()
            and not active_items.filter(verified=False).exists()
        ):
            report_ready_count += 1

    context = {
        "orders": recent_orders,

        "query": query,
        "status_filter": status_filter,
        "priority_filter": priority_filter,

        "total_count": total_count,
        "requested_count": requested_count,
        "received_count": received_count,
        "collected_count": collected_count,
        "processing_count": processing_count,
        "verification_count": verification_count,
        "completed_count": completed_count,
        "cancelled_count": cancelled_count,
        "report_ready_count": report_ready_count,
        "sent_orders_count": sent_orders_count,
        "received_orders_count": received_orders_count,
        "integrity_problem_items": integrity_problem_items[:100],
        "integrity_problem_count": integrity_problem_count,

        "urgent_count": urgent_count,
        "stat_count": stat_count,

        "department_stats": department_stats,

        "status_labels": status_labels,
        "priority_labels": priority_labels,
    }

    return render(
        request,
        "laboratory/dashboard.html",
        context
    )


# ============================================================
# Create Laboratory Order
# ============================================================

@login_required
@transaction.atomic
def create_laboratory_order(request, visit_id=None, admission_id=None):
    if not lab_require_permission(
        request,
        "laboratory.create_order",
        "ليس لديك صلاحية إنشاء طلب فحص مخبري.",
    ):
        return redirect("laboratory:dashboard")

    admission = None
    visit = None

    # ------------------------------------------------------------
    # Create order from inpatient admission
    # ------------------------------------------------------------
    if admission_id is not None:
        admission = get_object_or_404(
            Admission.objects.select_related(
                "patient",
                "visit",
                "department",
                "doctor",
            ),
            id=admission_id,
        )

        if admission.status != "ADMITTED":
            messages.error(
                request,
                "لا يمكن إنشاء طلب مختبر من تنويم غير نشط."
            )
            return redirect(
                "inpatient:admission_detail",
                admission_id=admission.id,
            )

        visit = admission.visit

    # ------------------------------------------------------------
    # Existing outpatient/visit workflow
    # ------------------------------------------------------------
    elif visit_id is not None:
        visit = get_object_or_404(
            Visit.objects.select_related(
                "patient",
                "department",
                "doctor",
            ),
            id=visit_id,
        )

        # PHASE 12.5.2.4 — DEPARTMENT ISOLATION
        # A non-manager user may create a laboratory order
        # only from a visit belonging to their own department.
        #
        # ADMIN / MANAGER retain cross-department access.
        #
        # A visit without a department is not a trusted
        # department-originated workflow for operational users.

        if not is_lab_manager(request.user):
            user_department = get_user_lab_department(request.user)

            if (
                not user_department
                or not visit.department
                or user_department.id != visit.department_id
            ):
                messages.error(
                    request,
                    "لا يمكنك إنشاء طلب مختبر لزيارة تابعة لقسم آخر."
                )
                return redirect("departments:list")

    else:
        messages.error(request, "لم يتم تحديد المريض أو التنويم.")
        return redirect("laboratory:dashboard")

    tests = (
        LaboratoryTest.objects
        .filter(is_active=True)
        .select_related("department")
        .order_by(
            "department__name_ar",
            "name_en",
        )
    )

    if request.method == "POST":

        selected_tests = request.POST.getlist("tests")

        if not selected_tests:
            messages.error(
                request,
                "يجب اختيار فحص مخبري واحد على الأقل."
            )
            return render(
                request,
                "laboratory/create_order.html",
                {
                    "visit": visit,
                    "admission": admission,
                    "tests": tests,
                }
            )

        # --------------------------------------------------------
        # Generate unique laboratory order number
        # --------------------------------------------------------

        last_order = (
            LaboratoryOrder.objects
            .order_by("-id")
            .first()
        )

        next_number = 1

        if last_order:
            try:
                old_number = int(
                    str(last_order.order_number)
                    .replace("LAB-", "")
                )
                next_number = old_number + 1
            except (ValueError, AttributeError):
                next_number = last_order.id + 1

        while LaboratoryOrder.objects.filter(
            order_number=f"LAB-{next_number:06d}"
        ).exists():
            next_number += 1

        order_number = f"LAB-{next_number:06d}"

        # --------------------------------------------------------
        # Priority
        # --------------------------------------------------------

        priority = request.POST.get(
            "priority",
            "NORMAL"
        )

        if priority not in {
            "NORMAL",
            "URGENT",
            "STAT",
        }:
            priority = "NORMAL"

        # --------------------------------------------------------
        # Clinical notes
        # --------------------------------------------------------

        clinical_notes = request.POST.get(
            "clinical_notes",
            ""
        ).strip()

        # --------------------------------------------------------
        # Determine patient / department / doctor
        # --------------------------------------------------------

        if admission is not None:
            patient = admission.patient
            requesting_department = admission.department
            requesting_doctor = admission.doctor
        else:
            patient = visit.patient
            requesting_department = visit.department
            requesting_doctor = visit.doctor

        # --------------------------------------------------------
        # Create order
        # --------------------------------------------------------

        order = LaboratoryOrder.objects.create(
            order_number=order_number,
            patient=patient,
            visit=visit,
            admission=admission,
            requesting_department=requesting_department,
            requesting_doctor=requesting_doctor,
            priority=priority,
            clinical_notes=clinical_notes,
            status="REQUESTED",
        )

        # --------------------------------------------------------
        # Add selected tests
        # --------------------------------------------------------

        valid_tests = list(LaboratoryTest.objects.filter(
            id__in=set(selected_tests),
            is_active=True,
        ))

        # لا ننشئ طلباً فارغاً أو بفحوصات غير صالحة حتى لو تم تعديل الطلب يدوياً.
        if not valid_tests:
            messages.error(
                request,
                "الفحوصات المحددة غير صالحة أو لم تعد متاحة. اختر فحصاً نشطاً واحداً على الأقل."
            )
            return render(
                request,
                "laboratory/create_order.html",
                {"visit": visit, "admission": admission, "tests": tests},
            )

        for test in valid_tests:
            LaboratoryOrderItem.objects.create(
                order=order,
                test=test,
                status="REQUESTED",
            )

        messages.success(
            request,
            f"تم إنشاء طلب المختبر {order_number} بنجاح."
        )

        return redirect(
            "laboratory:order_detail",
            order_id=order.id
        )

    return render(
        request,
        "laboratory/create_order.html",
        {
            "visit": visit,
            "admission": admission,
            "tests": tests,
        }
    )


# ============================================================
# Laboratory Order Detail
# ============================================================

@login_required
@transaction.atomic
def laboratory_order_detail(request, order_id):

    if not lab_require_permission(
        request,
        "laboratory.orders.view",
        "ليس لديك صلاحية عرض طلبات المختبر.",
    ):
        return redirect("laboratory:dashboard")

    order = get_object_or_404(
        LaboratoryOrder.objects
        .select_related(
            "patient",
            "visit",
            "admission",
            "requesting_department",
            "requesting_doctor",
        )
        .prefetch_related(
            "items__test",
            "items__examiner",
            "items__verified_by",
        ),
        id=order_id,
    )

    # ========================================================
    # Department-scoped order items
    # ========================================================
    if is_lab_manager(request.user):
        items = order.items.all()
    else:
        user_department = get_user_lab_department(request.user)

        if not user_department:
            return lab_access_denied(
                request,
                "لا يوجد قسم مختبر مرتبط بحسابك."
            )

        if user_department.code == "LAB":
            items = order.items.all()
        else:
            items = order.items.filter(
                test__department_id=user_department.id
            )

    if not items.exists():
        return lab_access_denied(
            request,
            "لا توجد فحوصات في هذا الطلب تابعة للقسم المسموح لحسابك."
        )

    if request.method == "POST":

        action = request.POST.get("action")

        # ====================================================
        # RECEIVE / COLLECT
        # ====================================================
        #
        # دورة العينات الرسمية تتم من خلال sample_reception.
        # لا نسمح لصفحة تفاصيل الطلب بتغيير حالة العينات مباشرة،
        # لأن الطلب قد يحتوي على فحوصات تابعة لأكثر من قسم.
        # ====================================================

        if action in {"receive", "collect"}:

            if not user_has_permission(
                request.user,
                "laboratory.sample.receive",
            ):
                messages.error(
                    request,
                    "ليس لديك صلاحية استلام أو سحب العينات.",
                )
            else:
                messages.info(
                    request,
                    "تتم إدارة استلام وسحب العينات من صفحة استقبال العينات.",
                )

        # ====================================================
        # PROCESSING
        # ====================================================
        #
        # لا يتم تغيير حالة عناصر الطلب يدويًا من صفحة التفاصيل.
        # بعد سحب العينة يتم إدخال النتائج من صفحة النتائج.
        # ====================================================

        elif action == "processing":

            if not (
                user_has_permission(
                    request.user,
                    "laboratory.results.enter",
                )
                or user_has_permission(
                    request.user,
                    "laboratory.results.edit",
                )
            ):
                messages.error(
                    request,
                    "ليس لديك صلاحية بدء معالجة نتائج المختبر.",
                )
            else:
                messages.info(
                    request,
                    "تتم معالجة النتائج من صفحة إدخال النتائج.",
                )

        # ====================================================
        # CANCEL
        # ====================================================
        #
        # لا توجد حاليًا صلاحية مستقلة لإلغاء طلب مختبر.
        # لذلك لا ننفذ الإلغاء من صفحة التفاصيل لمنع منح
        # صلاحية جديدة ضمنيًا لمجرد امتلاك صلاحية العرض.
        # ====================================================

        elif action == "cancel":

            messages.error(
                request,
                "إلغاء طلبات المختبر غير متاح من هذه الصفحة.",
            )

        return redirect(
            "laboratory:order_detail",
            order_id=order.id,
        )

    return render(
        request,
        "laboratory/order_detail.html",
        {
            "order": order,
            "items": items,
        }
    )


# ============================================================
# Enter Results Page
# ============================================================

@login_required
@transaction.atomic
def enter_results(request, order_id):
    if not (
        user_has_permission(request.user, "laboratory.results.enter")
        or user_has_permission(request.user, "laboratory.results.edit")
    ):
        messages.error(
            request,
            "ليس لديك صلاحية إدخال أو تعديل النتائج."
        )
        return redirect("laboratory:dashboard")

    order = get_object_or_404(
        LaboratoryOrder.objects
        .select_related(
            "patient",
            "visit",
            "admission",
            "requesting_department",
            "requesting_doctor",
        )
        .prefetch_related(
            "items__test",
            "items__examiner",
        ),
        id=order_id,
    )

    if is_lab_manager(request.user):
        items = order.items.all()
    else:
        user_department = get_user_lab_department(request.user)

        if not user_department:
            return lab_access_denied(
                request,
                "لا يوجد قسم مختبر مرتبط بحسابك."
            )

        if user_department.code == "LAB":
            items = order.items.all()
        else:
            items = order.items.filter(
                test__department_id=user_department.id
            )

    if not items.exists():
        return lab_access_denied(
            request,
            "لا توجد فحوصات في هذا الطلب تابعة للقسم المسموح لحسابك."
        )

    if order.status == "COMPLETED":
        messages.warning(
            request,
            "لا يمكن تعديل النتائج بعد اعتماد الطلب."
        )
        return redirect(
            "laboratory:order_detail",
            order_id=order.id
        )

    if order.status == "CANCELLED":
        messages.warning(
            request,
            "هذا الطلب ملغى."
        )
        return redirect(
            "laboratory:order_detail",
            order_id=order.id
        )

    if request.method == "POST":

        # ----------------------------------------------------
        # تحديد هل توجد نتائج سابقة غير معتمدة
        # ----------------------------------------------------
        has_existing_result = any(
            (
                item.result
                and str(item.result).strip()
            )
            or item.result_numeric is not None
            for item in items
            if item.status != "CANCELLED"
            and not item.verified
        )

        if has_existing_result:
            if not user_has_permission(
                request.user,
                "laboratory.results.edit"
            ):
                messages.error(
                    request,
                    "ليس لديك صلاحية تعديل النتائج الموجودة."
                )
                return redirect(
                    "laboratory:order_detail",
                    order_id=order.id
                )
        else:
            if not user_has_permission(
                request.user,
                "laboratory.results.enter"
            ):
                messages.error(
                    request,
                    "ليس لديك صلاحية إدخال النتائج."
                )
                return redirect(
                    "laboratory:order_detail",
                    order_id=order.id
                )

        saved_count = 0

        # ====================================================
        # إدخال النتائج
        #
        # الفني يدخل Result فقط.
        #
        # مثال:
        # 15
        # 18.5
        # Positive
        # Negative
        #
        # إذا كانت القيمة رقمية:
        # Result Numeric + H/L/NORMAL + Critical
        # تحسب تلقائياً.
        # ====================================================
        for item in items:

            if item.status == "CANCELLED":
                continue

            if item.verified:
                continue

            if item.status not in {
                "COLLECTED",
                "PROCESSING",
            }:
                messages.warning(
                    request,
                    f"لا يمكن إدخال نتيجة للفحص "
                    f"{item.test.name_en}. "
                    f"حالة العينة الحالية: {item.status}"
                )
                continue

            # -----------------------------------------------
            # الحقل الوحيد الذي يدخله الفني
            # -----------------------------------------------
            result = request.POST.get(
                f"result_{item.id}",
                ""
            ).strip()

            examiner_notes = request.POST.get(
                f"examiner_notes_{item.id}",
                ""
            ).strip()

            # -----------------------------------------------
            # يجب إدخال Result
            # -----------------------------------------------
            if not result:
                messages.error(
                    request,
                    f"يجب إدخال نتيجة للفحص: "
                    f"{item.test.name_en}"
                )

                return render(
                    request,
                    "laboratory/enter_results.html",
                    {
                        "order": order,
                        "items": items,
                    }
                )

            item.result = result
            item.examiner_notes = examiner_notes

            # =================================================
            # اكتشاف القيمة الرقمية تلقائياً
            # =================================================
            numeric_value = None

            try:
                cleaned_result = (
                    result
                    .replace(",", "")
                    .strip()
                )

                numeric_value = Decimal(
                    cleaned_result
                )

            except (
                InvalidOperation,
                ValueError,
                TypeError,
            ):
                numeric_value = None

            # =================================================
            # نتيجة رقمية
            # =================================================
            if numeric_value is not None:

                item.result_numeric = numeric_value

                # ---------------------------------------------
                # H / L / NORMAL
                # ---------------------------------------------
                item.result_flag = calculate_result_flag(
                    item.result_numeric,
                    item.test.reference_range,
                )

                # ---------------------------------------------
                # Critical
                # ---------------------------------------------
                critical_status = calculate_critical_status(
                    item.result_numeric,
                    item.test,
                )

                item.critical_status = critical_status

                if critical_status:
                    item.critical_detected_at = timezone.now()
                else:
                    item.critical_detected_at = None

            # =================================================
            # نتيجة نصية
            # =================================================
            else:

                item.result_numeric = None
                item.result_flag = ""
                item.critical_status = ""
                item.critical_detected_at = None

            # =================================================
            # بيانات الفاحص
            # =================================================
            item.examiner = request.user
            item.examined_at = timezone.now()
            item.status = "PROCESSING"

            item.save(
                update_fields=[
                    "result",
                    "result_numeric",
                    "result_flag",
                    "critical_status",
                    "critical_detected_at",
                    "examiner_notes",
                    "examiner",
                    "examined_at",
                    "status",
                    "updated_at",
                ]
            )

            saved_count += 1

        # ====================================================
        # تحديث حالة الطلب
        # ====================================================
        # إدخال النتائج لا يعني اعتمادها.
        # يجب أن يبقى الطلب PROCESSING حتى يتم اعتماد
        # جميع الفحوصات الفعالة من خلال verify_results.
        # ====================================================

        order.status = "PROCESSING"

        order.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        messages.success(
            request,
            f"تم حفظ {saved_count} نتيجة بنجاح."
        )

        return redirect(
            "laboratory:order_detail",
            order_id=order.id
        )

    return render(
        request,
        "laboratory/enter_results.html",
        {
            "order": order,
            "items": items,
        }
    )

@login_required
@transaction.atomic
def verify_results(request, order_id):

    if not lab_require_permission(
        request,
        "laboratory.results.verify",
        "ليس لديك صلاحية اعتماد النتائج المخبرية.",
    ):
        return redirect("laboratory:dashboard")

    order = get_object_or_404(
        LaboratoryOrder.objects
        .select_related(
            "patient",
            "visit",
            "admission",
            "requesting_department",
            "requesting_doctor",
        )
        .prefetch_related(
            "items__test",
            "items__examiner",
            "items__verified_by",
        ),
        id=order_id,
    )

    # ========================================================
    # Department-scoped verification items
    # ========================================================
    if is_lab_manager(request.user):
        items = order.items.all()
    else:
        user_department = get_user_lab_department(request.user)

        if not user_department:
            return lab_access_denied(
                request,
                "لا يوجد قسم مختبر مرتبط بحسابك."
            )

        if user_department.code == "LAB":
            items = order.items.all()
        else:
            items = order.items.filter(
                test__department_id=user_department.id
            )

    if not items.exists():
        return lab_access_denied(
            request,
            "لا توجد فحوصات في هذا الطلب تابعة للقسم المسموح لحسابك."
        )

    if order.status == "COMPLETED":

        messages.warning(
            request,
            "هذا الطلب تم اعتماده مسبقًا."
        )

        return redirect(
            "laboratory:laboratory_report",
            order_id=order.id,
        )

    empty_items = []

    for item in items:

        if item.status == "CANCELLED":
            continue

        has_text = bool(
            item.result and item.result.strip()
        )

        has_numeric = (
            item.result_numeric is not None
        )

        if not has_text and not has_numeric:
            empty_items.append(
                item.test.name_en
            )

    if request.method == "POST":

        if empty_items:

            messages.error(
                request,
                "لا يمكن اعتماد النتائج. "
                "الفحوصات التالية بدون نتيجة: "
                + ", ".join(empty_items)
            )

            return redirect(
                "laboratory:enter_results",
                order_id=order.id,
            )

        now = timezone.now()
        verified_count = 0

        for item in items:

            if item.status == "CANCELLED":
                continue

            item.verified = True
            item.verified_at = now
            item.verified_by = request.user
            item.status = "COMPLETED"

            item.save(
                update_fields=[
                    "verified",
                    "verified_at",
                    "verified_by",
                    "status",
                    "updated_at",
                ]
            )

            verified_count += 1

        # ====================================================
        # Update overall order status safely
        # ====================================================
        # The order becomes COMPLETED only when ALL active items
        # across ALL laboratory departments are verified.
        # Otherwise it remains PROCESSING.
        # ====================================================

        all_items = order.items.all()

        active_items = all_items.exclude(
            status="CANCELLED"
        )

        all_verified = (
            active_items.exists()
            and not active_items.filter(
                verified=False
            ).exists()
        )

        if all_verified:
            order.status = "COMPLETED"
        else:
            order.status = "PROCESSING"

        order.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        messages.success(
            request,
            f"تم اعتماد {verified_count} نتيجة مخبرية بنجاح."
        )

        if all_verified:
            messages.success(
                request,
                "تم اعتماد جميع فحوصات الطلب وإغلاق الطلب."
            )
        else:
            messages.info(
                request,
                "تم اعتماد نتائج قسمك، وما زالت هناك فحوصات أخرى بانتظار الاعتماد."
            )

        return redirect(
            "laboratory:laboratory_report",
            order_id=order.id,
        )

    return render(
        request,
        "laboratory/verify_results.html",
        {
            "order": order,
            "items": items,
            "empty_items": empty_items,
        }
    )



# ============================================================
# Laboratory Result Workflow Dashboard
# ============================================================

@login_required
def result_workflow_dashboard(request):
    """
    لوحة متابعة دورة نتائج المختبر.
    للعرض والمتابعة فقط.
    لا تنشئ حالة جديدة ولا تعدل بيانات الطلبات أو النتائج.
    """

    if not lab_require_permission(
        request,
        "laboratory.results.verify",
        "ليس لديك صلاحية الوصول إلى لوحة متابعة نتائج المختبر.",
    ):
        return redirect("laboratory:dashboard")

    items = (
        LaboratoryOrderItem.objects
        .select_related(
            "order",
            "order__patient",
            "order__requesting_department",
            "order__requesting_doctor",
            "test",
            "test__department",
            "examiner",
            "verified_by",
        )
        .all()
    )

    # --------------------------------------------------------
    # Department scope
    # --------------------------------------------------------

    if not is_lab_manager(request.user):
        user_department = get_user_lab_department(request.user)

        if not user_department:
            return lab_access_denied(
                request,
                "لا يوجد قسم مختبر مرتبط بحسابك."
            )

        if user_department.code != "LAB":
            items = items.filter(
                test__department_id=user_department.id
            )

    # --------------------------------------------------------
    # Filters
    # --------------------------------------------------------

    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    verification = request.GET.get("verification", "").strip()
    department_id = request.GET.get("department_id", "").strip()
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()

    if q:
        items = items.filter(
            Q(order__order_number__icontains=q)
            | Q(order__patient__full_name__icontains=q)
            | Q(test__name_en__icontains=q)
            | Q(test__name_ar__icontains=q)
            | Q(sample_id__icontains=q)
        )

    if status:
        items = items.filter(status=status)

    if verification == "verified":
        items = items.filter(verified=True)
    elif verification == "pending":
        items = items.filter(verified=False)

    if department_id:
        items = items.filter(
            test__department_id=department_id
        )

    if date_from:
        items = items.filter(
            created_at__date__gte=date_from
        )

    if date_to:
        items = items.filter(
            created_at__date__lte=date_to
        )

    # --------------------------------------------------------
    # Active items
    # --------------------------------------------------------

    active_items = items.exclude(status="CANCELLED")

    total_items = active_items.count()

    # --------------------------------------------------------
    # Workflow statistics
    # --------------------------------------------------------

    requested_count = active_items.filter(
        status="REQUESTED"
    ).count()

    received_count = active_items.filter(
        status="RECEIVED"
    ).count()

    collected_count = active_items.filter(
        status="COLLECTED"
    ).count()

    processing_count = active_items.filter(
        status="PROCESSING"
    ).count()

    verified_count = active_items.filter(
        verified=True
    ).count()

    result_entered_count = active_items.filter(
        Q(result__isnull=False)
        & ~Q(result="")
    ).count()

    # النتائج الرقمية تعتبر أيضاً نتيجة مدخلة
    numeric_result_count = active_items.filter(
        result_numeric__isnull=False
    ).count()

    entered_count = active_items.filter(
        Q(result__isnull=False) & ~Q(result="")
        | Q(result_numeric__isnull=False)
    ).count()

    pending_verification_count = active_items.filter(
        verified=False
    ).filter(
        Q(result__isnull=False) & ~Q(result="")
        | Q(result_numeric__isnull=False)
    ).count()

    unverified_count = pending_verification_count

    completed_count = active_items.filter(
        status="COMPLETED"
    ).count()

    cancelled_count = items.filter(
        status="CANCELLED"
    ).count()

    # --------------------------------------------------------
    # IMPORTANT:
    # Define order_ids BEFORE using it.
    # --------------------------------------------------------

    order_ids = list(
        active_items
        .values_list("order_id", flat=True)
        .distinct()
    )

    # --------------------------------------------------------
    # Result delivery statistics
    # --------------------------------------------------------

    sent_order_ids = set(
        LaboratoryResultDelivery.objects
        .filter(order_id__in=order_ids)
        .values_list("order_id", flat=True)
        .distinct()
    )

    received_order_ids = set(
        LaboratoryResultDelivery.objects
        .filter(
            order_id__in=order_ids,
            received=True,
        )
        .values_list("order_id", flat=True)
        .distinct()
    )

    sent_orders_count = len(sent_order_ids)

    received_orders_count = len(received_order_ids)

    # الإحصائية القديمة الخاصة بعدد الفحوصات التابعة لطلبات مرسلة
    sent_count = active_items.filter(
        order_id__in=sent_order_ids
    ).count()

    # --------------------------------------------------------
    # Report readiness
    # --------------------------------------------------------

    # حساب الطلبات الجاهزة للتقرير بدون استخدام Count
    # حتى لا نعتمد على استيراد django.db.models.Count.
    # هذا الحساب للعرض فقط ولا يعدل أي بيانات.
    report_ready_order_ids = set()

    for oid in set(order_ids):
        order_active_items = (
            LaboratoryOrderItem.objects
            .filter(order_id=oid)
            .exclude(status="CANCELLED")
        )

        if (
            order_active_items.exists()
            and not order_active_items.filter(verified=False).exists()
        ):
            report_ready_order_ids.add(oid)

    report_ready_count = len(report_ready_order_ids)

    # --------------------------------------------------------
    # Data integrity warnings
    # --------------------------------------------------------

    integrity_problem_items = (
        active_items
        .filter(status="COMPLETED")
        .filter(
            Q(verified=False)
            |
            (
                (
                    Q(result__isnull=True)
                    | Q(result="")
                )
                & Q(result_numeric__isnull=True)
            )
        )
        .select_related(
            "order",
            "order__patient",
            "test",
        )
        .order_by("-updated_at", "-id")
    )

    integrity_problem_count = integrity_problem_items.count()

    # --------------------------------------------------------
    # Departments / Doctors
    # --------------------------------------------------------

    departments = (
        Department.objects
        .filter(laboratory_tests__isnull=False)
        .distinct()
        .order_by("name_ar")
    )

    doctors = (
        Doctor.objects
        .filter(laboratory_orders__isnull=False)
        .distinct()
        .order_by("full_name")
    )

    status_choices = LaboratoryOrderItem.STATUS_CHOICES

    # --------------------------------------------------------
    # Context
    # --------------------------------------------------------

    context = {
        "items": active_items[:500],

        "total_items": total_items,

        "requested_count": requested_count,
        "received_count": received_count,
        "collected_count": collected_count,
        "processing_count": processing_count,

        "result_entered_count": result_entered_count,
        "numeric_result_count": numeric_result_count,
        "entered_count": entered_count,

        "verified_count": verified_count,
        "pending_verification_count": pending_verification_count,
        "unverified_count": unverified_count,

        "completed_count": completed_count,
        "cancelled_count": cancelled_count,

        "sent_count": sent_count,
        "sent_orders_count": sent_orders_count,
        "received_orders_count": received_orders_count,
        "report_ready_count": report_ready_count,

        "integrity_problem_items": integrity_problem_items[:100],
        "integrity_problem_count": integrity_problem_count,

        "departments": departments,
        "doctors": doctors,
        "status_choices": status_choices,

        "q": q,
        "status": status,
        "verification": verification,
        "department_id": department_id,
        "date_from": date_from,
        "date_to": date_to,
    }

    return render(
        request,
        "laboratory/result_workflow_dashboard.html",
        context,
    )


def report_settings(request):
    """
    إعدادات التقرير العامة.
    متاحة فقط لمدير النظام/مدير المستشفى
    مع صلاحية laboratory.report_settings.
    """

    if not lab_require_permission(
        request,
        "laboratory.report_settings",
        "ليس لديك صلاحية تعديل إعدادات تقارير المختبر.",
    ):
        return redirect("laboratory:dashboard")

    if not is_lab_manager(request.user):
        return lab_access_denied(
            request,
            "هذه الصفحة متاحة لمدير النظام أو مدير المستشفى فقط."
        )

    settings_obj, _ = LaboratoryReportSettings.objects.get_or_create(pk=1)

    if request.method == "POST":

        # =====================================================
        # Helper functions
        # =====================================================

        def post_text(name):
            return request.POST.get(name, "").strip()

        def post_bool(name):
            # checkbox غير محدد لا يظهر في POST
            return name in request.POST

        def post_decimal(name, current_value):
            raw = request.POST.get(name, "").strip()

            if raw == "":
                return current_value

            try:
                return Decimal(raw)
            except (InvalidOperation, ValueError):
                messages.error(
                    request,
                    f"القيمة الرقمية للحقل {name} غير صحيحة."
                )
                return current_value

        # =====================================================
        # Report language and test-name display
        # =====================================================

        report_language = post_text("report_language")
        if report_language in ("AR", "EN", "BOTH"):
            settings_obj.report_language = report_language

        test_name_language = post_text("test_name_language")
        if test_name_language in ("AR", "EN", "BOTH"):
            settings_obj.test_name_language = test_name_language

        test_name_display = post_text("test_name_display")
        if test_name_display in ("FULL", "SHORT", "FULL_SHORT"):
            settings_obj.test_name_display = test_name_display

        # =====================================================
        # Report table column widths
        # =====================================================

        settings_obj.auto_column_widths = post_bool(
            "auto_column_widths"
        )

        column_width_fields = [
            "column_width_number",
            "column_width_test",
            "column_width_test_code",
            "column_width_result",
            "column_width_unit",
            "column_width_reference",
            "column_width_flag",
            "column_width_critical",
            "column_width_sample",
            "column_width_device",
            "column_width_reagent",
        ]

        for field_name in column_width_fields:
            setattr(
                settings_obj,
                field_name,
                post_decimal(
                    field_name,
                    getattr(settings_obj, field_name),
                ),
            )

        # =====================================================
        # Facility information
        # =====================================================

        settings_obj.hospital_name_ar = post_text("hospital_name_ar")
        settings_obj.hospital_name_en = post_text("hospital_name_en")

        settings_obj.laboratory_name_ar = post_text("laboratory_name_ar")
        settings_obj.laboratory_name_en = post_text("laboratory_name_en")

        settings_obj.address = post_text("address")
        settings_obj.phone = post_text("phone")
        settings_obj.email = post_text("email")

        # =====================================================
        # Report titles
        # =====================================================

        settings_obj.report_title_ar = post_text("report_title_ar")
        settings_obj.report_title_en = post_text("report_title_en")

        settings_obj.report_subtitle_ar = post_text(
            "report_subtitle_ar"
        )
        settings_obj.report_subtitle_en = post_text(
            "report_subtitle_en"
        )

        # =====================================================
        # Report metadata
        # =====================================================

        boolean_fields = [
            "show_report_number",
            "show_report_date",
            "show_report_time",
            "show_generated_datetime",

            "show_patient_number",
            "show_patient_name",
            "show_patient_age",
            "show_patient_gender",
            "show_patient_phone",
            "show_patient_address",
            "show_visit_number",

            "show_requesting_department",
            "show_requesting_doctor",

            "show_test_code",
            "show_test_name",
            "show_result",
            "show_unit",
            "show_reference_range",
            "show_result_flag",
            "show_critical_status",
            "show_sample_type",
            "show_device",
            "show_reagent",

            "show_examiner_notes",

            "show_examiner_signature",
            "show_verifier_signature",
            "show_director_signature",

            "show_footer",

            "show_logo",
            "watermark_enabled",

            "show_page_number",
            "show_print_datetime",
            "print_color",

            "rtl_layout",
        ]

        for field_name in boolean_fields:
            if hasattr(settings_obj, field_name):
                setattr(
                    settings_obj,
                    field_name,
                    post_bool(field_name),
                )

        # =====================================================
        # Signature labels
        # =====================================================

        settings_obj.examiner_signature_label = post_text(
            "examiner_signature_label"
        )

        settings_obj.verifier_signature_label = post_text(
            "verifier_signature_label"
        )

        settings_obj.director_signature_label = post_text(
            "director_signature_label"
        )

        # =====================================================
        # Footer
        # =====================================================

        settings_obj.report_footer = post_text("report_footer")
        settings_obj.report_footer_en = post_text("report_footer_en")

        # =====================================================
        # Colors
        # =====================================================

        color_fields = [
            "accent_color",
            "table_header_color",
            "table_header_text_color",
            "report_background_color",
        ]

        for field_name in color_fields:
            value = post_text(field_name)

            if value:
                setattr(settings_obj, field_name, value)

        # =====================================================
        # Logo position
        # =====================================================

        logo_position = post_text("logo_position")

        if logo_position in {"LEFT", "CENTER", "RIGHT"}:
            settings_obj.logo_position = logo_position

        # =====================================================
        # Watermark
        # =====================================================

        settings_obj.watermark_text = post_text(
            "watermark_text"
        )

        settings_obj.watermark_opacity = post_decimal(
            "watermark_opacity",
            settings_obj.watermark_opacity,
        )

        # =====================================================
        # Paper / printing
        # =====================================================

        paper_size = post_text("paper_size")

        if paper_size in {"A4", "A5", "LETTER"}:
            settings_obj.paper_size = paper_size

        orientation = post_text("orientation")

        if orientation in {"PORTRAIT", "LANDSCAPE"}:
            settings_obj.orientation = orientation

        # =====================================================
        # Margins
        # =====================================================

        settings_obj.margin_top = post_decimal(
            "margin_top",
            settings_obj.margin_top,
        )

        settings_obj.margin_bottom = post_decimal(
            "margin_bottom",
            settings_obj.margin_bottom,
        )

        settings_obj.margin_left = post_decimal(
            "margin_left",
            settings_obj.margin_left,
        )

        settings_obj.margin_right = post_decimal(
            "margin_right",
            settings_obj.margin_right,
        )

        # =====================================================
        # Font sizes
        # =====================================================

        settings_obj.report_font_size = post_decimal(
            "report_font_size",
            settings_obj.report_font_size,
        )

        settings_obj.table_font_size = post_decimal(
            "table_font_size",
            settings_obj.table_font_size,
        )

        # =====================================================
        # Logo upload
        # =====================================================

        uploaded_logo = request.FILES.get("logo")

        if uploaded_logo:
            settings_obj.logo = uploaded_logo

        # =====================================================
        # Save
        # =====================================================

        settings_obj.save()

        messages.success(
            request,
            "تم حفظ جميع إعدادات تقرير المختبر بنجاح."
        )

        return redirect(
            "laboratory:report_settings"
        )

    return render(
        request,
        "laboratory/report_settings.html",
        {
            "settings": settings_obj,
        }
    )

def receive_result(request, delivery_id):
    """
    تأكيد استلام نتيجة المختبر.
    لا يتم تعديل نتيجة الفحص الأصلية.
    يتم فقط تحديث سجل تسليم النتيجة.
    """

    if request.method != "POST":
        messages.warning(
            request,
            "يجب استخدام زر تأكيد الاستلام.",
        )
        return redirect("laboratory:dashboard")

    if not lab_require_permission(
        request,
        "laboratory.results.verify",
        "ليس لديك صلاحية تأكيد استلام النتائج المخبرية.",
    ):
        return redirect("laboratory:dashboard")

    delivery = get_object_or_404(
        LaboratoryResultDelivery.objects.select_related(
            "order",
            "order__patient",
            "department",
            "doctor",
        ),
        id=delivery_id,
    )

    if delivery.received:
        messages.info(
            request,
            "هذه النتيجة تم تأكيد استلامها مسبقًا.",
        )
        return redirect(
            "laboratory:send_result",
            order_id=delivery.order_id,
        )

    delivery.received = True
    delivery.received_at = timezone.now()
    delivery.received_by = request.user
    delivery.save(
        update_fields=[
            "received",
            "received_at",
            "received_by",
        ]
    )

    destination_parts = []

    if delivery.department:
        destination_parts.append(
            f"القسم: {delivery.department.name_ar} - {delivery.department.name_en}"
        )

    if delivery.doctor:
        destination_parts.append(
            f"الطبيب: {delivery.doctor.full_name}"
        )

    create_laboratory_audit_log(
        request,
        "RECEIVE_RESULT",
        order=delivery.order,
        description=(
            "تم تأكيد استلام نتيجة المختبر من "
            + " و ".join(destination_parts)
            + f" | Delivery ID: {delivery.id}"
        ),
    )

    messages.success(
        request,
        "تم تأكيد استلام نتيجة المختبر بنجاح.",
    )

    return redirect(
        "laboratory:send_result",
        order_id=delivery.order_id,
    )



@login_required
def result_delivery_dashboard(request):
    """
    لوحة متابعة إرسال واستلام نتائج المختبر.
    قراءة فقط: لا تعدل أو تحذف أي نتيجة أو سجل تسليم.
    """

    if not lab_require_permission(
        request,
        "laboratory.results.verify",
        "ليس لديك صلاحية الدخول إلى لوحة متابعة النتائج.",
    ):
        return redirect("laboratory:dashboard")

    deliveries = (
        LaboratoryResultDelivery.objects
        .select_related(
            "order",
            "order__patient",
            "department",
            "doctor",
            "sent_by",
            "received_by",
        )
        .all()
    )

    # البحث
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    department_id = request.GET.get("department_id", "").strip()
    doctor_id = request.GET.get("doctor_id", "").strip()
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()

    if q:
        deliveries = deliveries.filter(
            Q(order__order_number__icontains=q)
            | Q(order__patient__full_name__icontains=q)
        )

    if status == "received":
        deliveries = deliveries.filter(received=True)
    elif status == "pending":
        deliveries = deliveries.filter(received=False)

    if department_id:
        deliveries = deliveries.filter(
            department_id=department_id
        )

    if doctor_id:
        deliveries = deliveries.filter(
            doctor_id=doctor_id
        )

    # تصفية صحيحة للتاريخ:
    if date_from:
        deliveries = deliveries.filter(
            sent_at__date__gte=date_from
        )

    if date_to:
        deliveries = deliveries.filter(
            sent_at__date__lte=date_to
        )

    # الإحصائيات
    all_deliveries = LaboratoryResultDelivery.objects.all()

    total_count = all_deliveries.count()
    received_count = all_deliveries.filter(received=True).count()
    pending_count = all_deliveries.filter(received=False).count()

    from django.utils import timezone

    today = timezone.localdate()

    today_count = all_deliveries.filter(
        sent_at__date=today
    ).count()

    context = {
        "deliveries": deliveries,
        "departments": Department.objects.all().order_by(
            "name_ar",
            "name_en",
        ),
        "doctors": Doctor.objects.all().order_by(
            "full_name"
        ),

        "q": q,
        "status": status,
        "department_id": department_id,
        "doctor_id": doctor_id,
        "date_from": date_from,
        "date_to": date_to,

        "total_count": total_count,
        "received_count": received_count,
        "pending_count": pending_count,
        "today_count": today_count,
    }

    return render(
        request,
        "laboratory/result_delivery_dashboard.html",
        context,
    )


@login_required
def laboratory_audit_dashboard(request):
    """
    لوحة سجل تدقيق عمليات المختبر.
    للعرض والمتابعة فقط ولا تعدّل أي بيانات.
    """

    if not lab_require_permission(
        request,
        "laboratory.results.verify",
        "ليس لديك صلاحية الوصول إلى سجل تدقيق المختبر.",
    ):
        return redirect("laboratory:dashboard")

    logs = LaboratoryAuditLog.objects.select_related(
        "order",
        "order__patient",
        "user",
    ).all()

    q = request.GET.get("q", "").strip()
    action = request.GET.get("action", "").strip()
    user_id = request.GET.get("user_id", "").strip()
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()

    if q:
        logs = logs.filter(
            Q(description__icontains=q)
            | Q(action__icontains=q)
            | Q(order__order_number__icontains=q)
            | Q(order__patient__full_name__icontains=q)
            | Q(user__username__icontains=q)
        )

    if action:
        logs = logs.filter(action=action)

    if user_id:
        logs = logs.filter(user_id=user_id)

    if date_from:
        logs = logs.filter(created_at__date__gte=date_from)

    if date_to:
        logs = logs.filter(created_at__date__lte=date_to)

    total_count = logs.count()

    today_count = logs.filter(
        created_at__date=timezone.localdate()
    ).count()

    users = (
        LaboratoryAuditLog.objects
        .filter(user__isnull=False)
        .values("user_id", "user__username")
        .distinct()
        .order_by("user__username")
    )

    action_choices = LaboratoryAuditLog.ACTION_CHOICES

    context = {
        "logs": logs[:500],
        "total_count": total_count,
        "today_count": today_count,
        "users": users,
        "action_choices": action_choices,
        "q": q,
        "action": action,
        "user_id": user_id,
        "date_from": date_from,
        "date_to": date_to,
    }

    return render(
        request,
        "laboratory/audit_dashboard.html",
        context,
    )


@login_required
def laboratory_audit_detail(request, log_id):
    """
    عرض تفاصيل سجل تدقيق واحد.
    للعرض فقط ولا يقوم بتعديل أو حذف السجل.
    """

    if not lab_require_permission(
        request,
        "laboratory.results.verify",
        "ليس لديك صلاحية الوصول إلى تفاصيل سجل تدقيق المختبر.",
    ):
        return redirect("laboratory:dashboard")

    log = get_object_or_404(
        LaboratoryAuditLog.objects.select_related(
            "order",
            "order__patient",
            "order__requesting_department",
            "order__requesting_doctor",
            "user",
        ),
        id=log_id,
    )

    return render(
        request,
        "laboratory/audit_detail.html",
        {
            "log": log,
        },
    )

def create_laboratory_audit_log(
    request,
    action,
    order=None,
    description="",
):
    """
    إنشاء سجل تدقيق لعملية مخبرية.
    لا يغيّر البيانات الأصلية.
    """

    ip_address = request.META.get("REMOTE_ADDR")

    return LaboratoryAuditLog.objects.create(
        order=order,
        user=request.user if request.user.is_authenticated else None,
        action=action,
        description=description,
        ip_address=ip_address,
    )


@login_required
@transaction.atomic
def send_result(request, order_id):
    """
    إرسال نتيجة المختبر المعتمدة إلى قسم أو طبيب.
    يتم تسجيل كل عملية إرسال كسجل مستقل.
    لا يتم تعديل نتيجة الفحص الأصلية.
    """

    if not lab_require_permission(
        request,
        "laboratory.results.verify",
        "ليس لديك صلاحية إرسال النتائج المخبرية.",
    ):
        return redirect("laboratory:dashboard")

    order = get_object_or_404(
        LaboratoryOrder.objects.select_related(
            "patient",
            "visit",
            "admission",
            "requesting_department",
            "requesting_doctor",
        ),
        id=order_id,
    )

    active_items = order.items.exclude(status="CANCELLED")

    # لا يسمح بإرسال تقرير غير مكتمل
    if (
        order.status != "COMPLETED"
        or not active_items.exists()
        or active_items.filter(verified=False).exists()
    ):
        messages.warning(
            request,
            "لا يمكن إرسال النتيجة قبل اكتمال واعتماد جميع نتائج الفحوصات.",
        )
        return redirect(
            "laboratory:order_detail",
            order_id=order.id,
        )

    departments = Department.objects.all().order_by("name_ar", "name_en")
    doctors = Doctor.objects.all().order_by("full_name")

    deliveries = (
        order.result_deliveries
        .select_related(
            "department",
            "doctor",
            "sent_by",
        )
        .all()
    )

    if request.method == "POST":
        department_id = request.POST.get("department_id", "").strip()
        doctor_id = request.POST.get("doctor_id", "").strip()
        note = request.POST.get("note", "").strip()

        if not department_id and not doctor_id:
            messages.error(
                request,
                "يجب اختيار القسم أو الطبيب الذي سيتم إرسال النتيجة إليه.",
            )

            return render(
                request,
                "laboratory/send_result.html",
                {
                    "order": order,
                    "departments": departments,
                    "doctors": doctors,
                    "deliveries": deliveries,
                    "selected_department": department_id,
                    "selected_doctor": doctor_id,
                    "note": note,
                },
            )

        department = None
        doctor = None

        if department_id:
            department = Department.objects.filter(
                pk=department_id
            ).first()

            if not department:
                messages.error(
                    request,
                    "القسم المحدد غير موجود.",
                )

                return render(
                    request,
                    "laboratory/send_result.html",
                    {
                        "order": order,
                        "departments": departments,
                        "doctors": doctors,
                        "deliveries": deliveries,
                        "selected_department": department_id,
                        "selected_doctor": doctor_id,
                        "note": note,
                    },
                )

        if doctor_id:
            doctor = Doctor.objects.filter(
                pk=doctor_id
            ).first()

            if not doctor:
                messages.error(
                    request,
                    "الطبيب المحدد غير موجود.",
                )

                return render(
                    request,
                    "laboratory/send_result.html",
                    {
                        "order": order,
                        "departments": departments,
                        "doctors": doctors,
                        "deliveries": deliveries,
                        "selected_department": department_id,
                        "selected_doctor": doctor_id,
                        "note": note,
                    },
                )

        delivery = LaboratoryResultDelivery.objects.create(
            order=order,
            department=department,
            doctor=doctor,
            sent_by=request.user,
            note=note,
        )

        destination_parts = []

        if department:
            destination_parts.append(
                f"القسم: {department.name_ar} - {department.name_en}"
            )

        if doctor:
            destination_parts.append(
                f"الطبيب: {doctor.full_name}"
            )

        create_laboratory_audit_log(
            request,
            "SEND_RESULT",
            order=order,
            description=(
                "تم إرسال نتيجة المختبر إلى "
                + " و ".join(destination_parts)
                + f" | Delivery ID: {delivery.id}"
            ),
        )

        destinations = []

        if department:
            destinations.append(
                f"القسم: {department.name_ar} - {department.name_en}"
            )

        if doctor:
            destinations.append(
                f"الطبيب: {doctor.full_name}"
            )

        messages.success(
            request,
            "تم إرسال نتيجة المختبر بنجاح إلى "
            + " و ".join(destinations)
            + ".",
        )

        return redirect(
            "laboratory:laboratory_report",
            order_id=order.id,
        )

    return render(
        request,
        "laboratory/send_result.html",
        {
            "order": order,
            "departments": departments,
            "doctors": doctors,
            "deliveries": deliveries,
        },
    )


def laboratory_report(request, order_id):
    if not lab_require_permission(
        request,
        "laboratory.reports.view",
        "ليس لديك صلاحية عرض تقارير المختبر.",
    ):
        return redirect("laboratory:dashboard")

    order = get_object_or_404(
        LaboratoryOrder.objects
        .select_related(
            "patient",
            "visit",
            "admission",
            "requesting_department",
            "requesting_doctor",
        )
        .prefetch_related(
            "items__test__department",
            "items__examiner",
            "items__verified_by",
        ),
        id=order_id,
    )

    # ========================================================
    # Laboratory Department Access Control
    # ========================================================
    if not user_can_access_order(request.user, order):
        return lab_access_denied(
            request,
            "ليس لديك صلاحية للوصول إلى تقرير هذا الطلب."
        )

    # المدير والمختبر المركزي يستطيعان رؤية جميع النتائج.
    # مستخدم القسم يرى فقط فحوصات قسمه.
    if is_lab_manager(request.user) or is_central_laboratory_user(request.user):
        items = list(order.items.all())
    else:
        user_department = get_user_lab_department(request.user)

        if not user_department:
            return lab_access_denied(
                request,
                "لا يوجد قسم مختبر مرتبط بحساب المستخدم."
            )

        items = list(
            order.items.filter(
                test__department_id=user_department.id
            )
        )

    # ========================================================
    # Group Results by Laboratory Department
    # ========================================================
    grouped_results = []
    group_map = {}

    for item in items:
        test = getattr(item, "test", None)
        department = getattr(test, "department", None)

        department_id = getattr(department, "id", None)

        if department_id not in group_map:
            group_map[department_id] = {
                "department": department,
                "items": [],
            }
            grouped_results.append(group_map[department_id])

        group_map[department_id]["items"].append(item)

    report_settings, _ = LaboratoryReportSettings.objects.get_or_create(
        pk=1
    )

    active_items = [
        item for item in items
        if getattr(item, "status", None) != "CANCELLED"
    ]

    can_send_result = (
        order.status == "COMPLETED"
        and bool(active_items)
        and not any(
            not getattr(item, "verified", False)
            for item in active_items
        )
    )

    return render(
        request,
        "laboratory/laboratory_report.html",
        {
            "order": order,
            "items": items,
            "grouped_results": grouped_results,
            "settings": report_settings,
            "report_settings": report_settings,
            "can_send_result": can_send_result,
        }
    )


def laboratory_report_pdf(request, order_id):
    """
    Professional Laboratory PDF Engine.

    Uses LaboratoryReportSettings for:
    - Paper size
    - Orientation
    - Margins
    - Colors
    - Font sizes
    - Logo
    - Watermark
    - Patient fields
    - Result columns
    - Critical values
    - Signatures
    - Footer
    - Page numbers
    """

    if not lab_require_permission(
        request,
        "laboratory.reports.pdf",
        "ليس لديك صلاحية إنشاء ملفات PDF لتقارير المختبر.",
    ):
        return redirect("laboratory:dashboard")

    order = get_object_or_404(
        LaboratoryOrder.objects
        .select_related(
            "patient",
            "visit",
            "admission",
            "requesting_department",
            "requesting_doctor",
        )
        .prefetch_related(
            "items__test__department",
            "items__examiner",
            "items__verified_by",
        ),
        id=order_id,
    )

    if not user_can_access_order(request.user, order):
        return lab_access_denied(
            request,
            "ليس لديك صلاحية الوصول إلى تقرير هذا الطلب."
        )

    # ---------------------------------------------------------
    # Department filtering
    # ---------------------------------------------------------

    if is_lab_manager(request.user) or is_central_laboratory_user(request.user):

        items = list(order.items.all())

    else:

        user_department = get_user_lab_department(request.user)

        if not user_department:
            return lab_access_denied(
                request,
                "لا يوجد قسم مختبر مرتبط بحساب المستخدم."
            )

        items = list(
            order.items.filter(
                test__department_id=user_department.id
            )
        )

    # ---------------------------------------------------------
    # Report settings
    # ---------------------------------------------------------

    settings_obj, _ = LaboratoryReportSettings.objects.get_or_create(pk=1)

    # ---------------------------------------------------------
    # Central Hospital Identity
    # ---------------------------------------------------------
    # System Settings has priority when a value exists.
    # Existing LaboratoryReportSettings values remain the
    # fallback so the current report is not affected when the
    # central settings are empty.

    hospital_identity = get_hospital_identity(
        {
            "name_ar": settings_obj.hospital_name_ar,
            "name_en": settings_obj.hospital_name_en,
            "address": settings_obj.address,
            "phone": settings_obj.phone,
            "email": settings_obj.email,
        }
    )


    # ---------------------------------------------------------
    # ReportLab imports
    # ---------------------------------------------------------

    from io import BytesIO

    from reportlab.lib import colors
    from reportlab.lib.colors import HexColor
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import A4, A5, LETTER, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        Image,
        KeepTogether,
    )

    # ---------------------------------------------------------
    # Arabic shaping
    # ---------------------------------------------------------

    try:
        import arabic_reshaper
        from bidi.algorithm import get_display

        def ar(value):
            if value is None:
                return ""

            value = str(value)

            if not value:
                return ""

            try:
                return get_display(arabic_reshaper.reshape(value))
            except Exception:
                return value

    except Exception:

        def ar(value):
            return "" if value is None else str(value)

    # ---------------------------------------------------------
    # Safe color helper
    # ---------------------------------------------------------

    def safe_color(value, default="#0d6efd"):

        if not value:
            value = default

        value = str(value).strip()

        if not re.match(
            r"^#[0-9A-Fa-f]{6}$",
            value
        ):
            value = default

        try:
            return HexColor(value)
        except Exception:
            return HexColor(default)

    accent = safe_color(
        settings_obj.accent_color,
        "#0d6efd"
    )

    table_header = safe_color(
        settings_obj.table_header_color,
        "#0d6efd"
    )

    table_text = safe_color(
        settings_obj.table_header_text_color,
        "#ffffff"
    )

    background_color = safe_color(
        settings_obj.report_background_color,
        "#ffffff"
    )

    # ---------------------------------------------------------
    # Paper size
    # ---------------------------------------------------------

    paper_map = {
        "A4": A4,
        "A5": A5,
        "LETTER": LETTER,
    }

    page_size = paper_map.get(
        settings_obj.paper_size,
        A4
    )

    if settings_obj.orientation == "LANDSCAPE":
        page_size = landscape(page_size)

    page_width, page_height = page_size

    # ---------------------------------------------------------
    # Margins
    # ---------------------------------------------------------

    margin_top = float(settings_obj.margin_top or 14) * mm
    margin_bottom = float(settings_obj.margin_bottom or 18) * mm
    margin_left = float(settings_obj.margin_left or 12) * mm
    margin_right = float(settings_obj.margin_right or 12) * mm

    # ---------------------------------------------------------
    # Fonts
    # ---------------------------------------------------------

    font_dir = Path(__file__).resolve().parent / "fonts"

    ar_font_path = font_dir / "NotoNaskhArabic-Regular.ttf"
    ar_bold_path = font_dir / "NotoNaskhArabic-Bold.ttf"

    AR_FONT = "Helvetica"
    AR_BOLD = "Helvetica-Bold"

    if ar_font_path.exists():

        try:
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont

            pdfmetrics.registerFont(
                TTFont(
                    "NotoNaskhArabic",
                    str(ar_font_path)
                )
            )

            AR_FONT = "NotoNaskhArabic"

            if ar_bold_path.exists():

                pdfmetrics.registerFont(
                    TTFont(
                        "NotoNaskhArabicBold",
                        str(ar_bold_path)
                    )
                )

                AR_BOLD = "NotoNaskhArabicBold"

        except Exception:
            pass

    # ---------------------------------------------------------
    # PDF response
    # ---------------------------------------------------------

    buffer = BytesIO()

    filename_number = (
        getattr(order, "order_number", None)
        or str(order.id)
    )

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'inline; filename="laboratory_report_{filename_number}.pdf"'
    )

    # ---------------------------------------------------------
    # Document
    # ---------------------------------------------------------
    # استخدام إعدادات التقرير الفعلية المحفوظة في الإدارة
    # Paper Size + Orientation + Margins
    # ---------------------------------------------------------

    doc = SimpleDocTemplate(
        buffer,
        pagesize=page_size,
        rightMargin=margin_right,
        leftMargin=margin_left,
        topMargin=margin_top,
        bottomMargin=margin_bottom,
        title=f"Laboratory Report - {order.order_number}",
        author="Hospital HIS / LIS",
    )

    # العرض الفعلي المتاح داخل الصفحة بعد خصم الهوامش.
    available_width = page_width - margin_left - margin_right

    # ---------------------------------------------------------
    # Styles
    # ---------------------------------------------------------

    report_font_size = float(
        settings_obj.report_font_size or 9.5
    )

    table_font_size = float(
        settings_obj.table_font_size or 7.5
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Normal"],
        fontName=AR_BOLD,
        fontSize=16,
        leading=20,
        alignment=TA_CENTER,
        textColor=accent,
        spaceAfter=3,
    )

    title_en_style = ParagraphStyle(
        "ReportTitleEN",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        alignment=TA_CENTER,
        textColor=accent,
    )

    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontName=AR_FONT,
        fontSize=8.5,
        leading=11,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#666666"),
    )

    hospital_ar_style = ParagraphStyle(
        "HospitalAR",
        parent=styles["Normal"],
        fontName=AR_BOLD,
        fontSize=14,
        leading=17,
        alignment=TA_CENTER,
    )

    hospital_en_style = ParagraphStyle(
        "HospitalEN",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        alignment=TA_CENTER,
    )

    section_style = ParagraphStyle(
        "Section",
        parent=styles["Normal"],
        fontName=AR_BOLD,
        fontSize=9,
        leading=12,
        textColor=table_text,
        alignment=TA_RIGHT,
    )

    body_ar_style = ParagraphStyle(
        "BodyAR",
        parent=styles["Normal"],
        fontName=AR_FONT,
        fontSize=report_font_size,
        leading=report_font_size + 3,
        alignment=TA_RIGHT,
    )

    body_en_style = ParagraphStyle(
        "BodyEN",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=report_font_size,
        leading=report_font_size + 3,
        alignment=TA_LEFT,
    )

    table_style = ParagraphStyle(
        "Table",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=table_font_size,
        leading=table_font_size + 2,
        alignment=TA_CENTER,
    )

    table_ar_style = ParagraphStyle(
        "TableAR",
        parent=styles["Normal"],
        fontName=AR_FONT,
        fontSize=table_font_size,
        leading=table_font_size + 2,
        alignment=TA_RIGHT,
    )

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def p_en(value, style=body_en_style):
        value = "-" if value in (None, "") else str(value)
        value = value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return Paragraph(value, style)

    def p_ar(value, style=body_ar_style):
        value = "-" if value in (None, "") else ar(value)
        value = (
            value
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        return Paragraph(value, style)

    def cell_value(value):
        if value is None or value == "":
            return "-"
        return str(value)

    # ---------------------------------------------------------
    # Story
    # ---------------------------------------------------------

    story = []

    # ---------------------------------------------------------
    # Header
    # ---------------------------------------------------------

    header_left = ""
    header_center = []
    header_right = ""

    if settings_obj.show_logo and settings_obj.logo:

        try:

            logo_path = settings_obj.logo.path

            if os.path.exists(logo_path):

                logo = Image(
                    logo_path,
                    width=22 * mm,
                    height=22 * mm,
                    kind="proportional",
                )

                if settings_obj.logo_position == "LEFT":
                    header_left = logo

                elif settings_obj.logo_position == "RIGHT":
                    header_right = logo

                else:
                    header_center.append(logo)

        except Exception:
            pass

    if hospital_identity["name_ar"]:
        header_center.append(
            Paragraph(
                ar(hospital_identity["name_ar"]),
                hospital_ar_style,
            )
        )

    if hospital_identity["name_en"]:
        header_center.append(
            Paragraph(
                str(hospital_identity["name_en"]),
                hospital_en_style,
            )
        )

    if settings_obj.laboratory_name_ar:
        header_center.append(
            Paragraph(
                ar(settings_obj.laboratory_name_ar),
                ParagraphStyle(
                    "LabAR",
                    parent=hospital_ar_style,
                    fontSize=11,
                    leading=14,
                ),
            )
        )

    if settings_obj.laboratory_name_en:
        header_center.append(
            Paragraph(
                str(settings_obj.laboratory_name_en),
                ParagraphStyle(
                    "LabEN",
                    parent=hospital_en_style,
                    fontSize=8,
                    leading=10,
                ),
            )
        )

    if settings_obj.logo_position == "CENTER" and settings_obj.show_logo and settings_obj.logo:

        try:

            logo_path = settings_obj.logo.path

            if os.path.exists(logo_path):

                header_center.insert(
                    0,
                    Image(
                        logo_path,
                        width=20 * mm,
                        height=20 * mm,
                        kind="proportional",
                    )
                )

        except Exception:
            pass

    if header_center:

        center_table = Table(
            [[x] for x in header_center],
            colWidths=[95 * mm],
        )

        center_table.setStyle(
            TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ])
        )

    else:
        center_table = ""

    header_table = Table(
        [[header_left, center_table, header_right]],
        colWidths=[
            35 * mm,
            100 * mm,
            35 * mm,
        ],
    )

    header_table.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (0, 0), "LEFT"),
            ("ALIGN", (1, 0), (1, 0), "CENTER"),
            ("ALIGN", (2, 0), (2, 0), "RIGHT"),
            ("LINEBELOW", (0, 0), (-1, -1), 2, accent),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ])
    )

    story.append(header_table)
    story.append(Spacer(1, 5 * mm))

    # ---------------------------------------------------------
    # Title
    # ---------------------------------------------------------

    if settings_obj.report_title_ar:
        story.append(
            Paragraph(
                ar(settings_obj.report_title_ar),
                title_style,
            )
        )

    if settings_obj.report_title_en:
        story.append(
            Paragraph(
                str(settings_obj.report_title_en),
                title_en_style,
            )
        )

    if settings_obj.report_subtitle_ar:
        story.append(
            Paragraph(
                ar(settings_obj.report_subtitle_ar),
                subtitle_style,
            )
        )

    if settings_obj.report_subtitle_en:
        story.append(
            Paragraph(
                str(settings_obj.report_subtitle_en),
                subtitle_style,
            )
        )

    story.append(Spacer(1, 4 * mm))

    # ---------------------------------------------------------
    # Report metadata
    # ---------------------------------------------------------

    meta = []

    if settings_obj.show_report_number:

        meta.append([
            p_en("Report Number"),
            p_en(
                getattr(order, "order_number", None)
                or str(order.id)
            )
        ])

    if settings_obj.show_report_date:

        requested_at = getattr(
            order,
            "requested_at",
            None
        )

        meta.append([
            p_en("Report Date"),
            p_en(
                requested_at.strftime("%Y-%m-%d")
                if requested_at
                else "-"
            )
        ])

    if settings_obj.show_report_time:

        requested_at = getattr(
            order,
            "requested_at",
            None
        )

        meta.append([
            p_en("Report Time"),
            p_en(
                requested_at.strftime("%H:%M")
                if requested_at
                else "-"
            )
        ])

    if settings_obj.show_generated_datetime:

        meta.append([
            p_en("Generated"),
            p_en(
                timezone.localtime().strftime(
                    "%Y-%m-%d %H:%M"
                )
            )
        ])

    if meta:

        meta_table = Table(
            meta,
            colWidths=[
                45 * mm,
                45 * mm,
            ],
        )

        meta_table.setStyle(
            TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d9dee3")),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f5f7fa")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ])
        )

        story.append(
            Table(
                [[meta_table]],
                colWidths=[90 * mm],
                hAlign="CENTER",
            )
        )

        story.append(Spacer(1, 4 * mm))

    # ---------------------------------------------------------
    # Patient information
    # ---------------------------------------------------------

    patient = order.patient

    patient_data = []

    def add_patient_field(label, value):

        patient_data.append([
            p_ar(label),
            p_ar(cell_value(value)),
        ])

    if settings_obj.show_patient_number:
        add_patient_field(
            "رقم المريض",
            getattr(patient, "patient_number", None)
            or getattr(patient, "id", None)
        )

    if settings_obj.show_patient_name:
        add_patient_field(
            "اسم المريض",
            getattr(patient, "full_name", None)
        )

    if settings_obj.show_patient_age:
        add_patient_field(
            "العمر",
            getattr(patient, "age", None)
        )

    if settings_obj.show_patient_gender:
        add_patient_field(
            "الجنس",
            getattr(patient, "gender", None)
        )

    if settings_obj.show_patient_phone:
        add_patient_field(
            "الهاتف",
            getattr(patient, "phone", None)
        )

    if settings_obj.show_patient_address:
        add_patient_field(
            "العنوان",
            getattr(patient, "address", None)
        )

    if settings_obj.show_visit_number:

        visit_number = getattr(
            order.visit,
            "id",
            None
        ) if getattr(order, "visit", None) else None

        add_patient_field(
            "رقم الزيارة",
            visit_number
        )

    if settings_obj.show_requesting_department:

        department = getattr(
            order,
            "requesting_department",
            None
        )

        department_name = "-"

        if department:

            department_name = (
                getattr(
                    department,
                    "name_ar",
                    None
                )
                or getattr(
                    department,
                    "name",
                    None
                )
                or "-"
            )

        add_patient_field(
            "القسم الطالب",
            department_name
        )

    if settings_obj.show_requesting_doctor:

        add_patient_field(
            "الطبيب الطالب",
            str(
                order.requesting_doctor
            )
            if order.requesting_doctor
            else "-"
        )

    if patient_data:

        section_header = Table(
            [[Paragraph(
                ar("بيانات المريض / Patient Information"),
                section_style
            )]],
            colWidths=[170 * mm],
        )

        section_header.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), table_header),
                ("BOX", (0, 0), (-1, -1), 0.5, table_header),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ])
        )

        story.append(section_header)

        # 2 columns of fields
        rows = []

        for index in range(0, len(patient_data), 2):

            row = patient_data[index:index + 2]

            while len(row) < 2:
                row.append(["", ""])

            rows.append([
                row[0][0],
                row[0][1],
                row[1][0],
                row[1][1],
            ])

        patient_table = Table(
            rows,
            colWidths=[
                28 * mm,
                57 * mm,
                28 * mm,
                57 * mm,
            ],
        )

        patient_table.setStyle(
            TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d9dee3")),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f7f8fa")),
                ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#f7f8fa")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ])
        )

        story.append(patient_table)
        story.append(Spacer(1, 4 * mm))

    # ---------------------------------------------------------
    # Results
    # ---------------------------------------------------------
    # Group laboratory results by laboratory department
    # ---------------------------------------------------------

    grouped_results = []
    group_map = {}

    for item in items:
        department = getattr(item.test, "department", None)
        department_id = getattr(department, "id", None)

        if department_id not in group_map:
            group_map[department_id] = {
                "department": department,
                "items": [],
            }
            grouped_results.append(group_map[department_id])

        group_map[department_id]["items"].append(item)

    # ---------------------------------------------------------
    # Results section title
    # ---------------------------------------------------------

    story.append(
        Table(
            [[Paragraph(
                ar("نتائج الفحوصات / Laboratory Results"),
                section_style
            )]],
            colWidths=[available_width],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), table_header),
                ("BOX", (0, 0), (-1, -1), 0.5, table_header),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]),
        )
    )

    # ---------------------------------------------------------
    # One table for each laboratory department
    # ---------------------------------------------------------

    for group in grouped_results:

        department = group["department"]
        department_items = group["items"]

        department_name_en = (
            getattr(department, "name_en", None)
            if department
            else None
        ) or "Unassigned Laboratory"

        # Department heading - English only
        department_title = Table(
            [[
                Paragraph(
                    str(department_name_en),
                    table_style
                ),
            ]],
            colWidths=[
                available_width,
            ],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eef3f7")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cfd6dd")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (0, 0), "LEFT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]),
        )

        story.append(Spacer(1, 5))
        story.append(department_title)
        story.append(Spacer(1, 3))

        # -----------------------------------------------------
        # Dynamic columns
        # -----------------------------------------------------

        headers = [p_en("#", table_style)]
        column_keys = ["number"]

        if settings_obj.show_test_name:
            headers.append(p_en("Test", table_style))
            column_keys.append("test")

        if settings_obj.show_test_code:
            headers.append(p_en("Code", table_style))
            column_keys.append("test_code")

        if settings_obj.show_result:
            headers.append(p_en("Result", table_style))
            column_keys.append("result")

        if settings_obj.show_unit:
            headers.append(p_en("Unit", table_style))
            column_keys.append("unit")

        if settings_obj.show_reference_range:
            headers.append(p_en("Reference Range", table_style))
            column_keys.append("reference")

        if settings_obj.show_result_flag:
            headers.append(p_en("Flag", table_style))
            column_keys.append("flag")

        if settings_obj.show_critical_status:
            headers.append(p_en("Critical", table_style))
            column_keys.append("critical")

        if settings_obj.show_sample_type:
            headers.append(p_en("Sample", table_style))
            column_keys.append("sample")

        if settings_obj.show_device:
            headers.append(p_en("Device", table_style))
            column_keys.append("device")

        if settings_obj.show_reagent:
            headers.append(p_en("Reagent", table_style))
            column_keys.append("reagent")

        result_data = [headers]

        for index, item in enumerate(department_items, start=1):

            test = item.test

            result_value = "-"
            if item.result_numeric is not None:
                result_value = str(item.result_numeric)
            elif item.result:
                result_value = str(item.result)

            row = []

            for key in column_keys:

                if key == "number":
                    row.append(
                        p_en(index, table_style)
                    )

                elif key == "test":
                    # -------------------------------------------------
                    # -------------------------------------------------
                    # Test name language / short-name display
                    # -------------------------------------------------

                    name_en = (
                        getattr(test, "name_en", None)
                        or ""
                    ).strip()

                    name_ar = (
                        getattr(test, "name_ar", None)
                        or ""
                    ).strip()

                    short_en = (
                        getattr(test, "short_name_en", None)
                        or ""
                    ).strip()

                    short_ar = (
                        getattr(test, "short_name_ar", None)
                        or ""
                    ).strip()

                    # Safe fallback for old tests that have no short name.
                    if not short_en:
                        short_en = name_en

                    if not short_ar:
                        short_ar = name_ar

                    name_language = getattr(
                        settings_obj,
                        "test_name_language",
                        "EN"
                    )

                    name_display = getattr(
                        settings_obj,
                        "test_name_display",
                        "FULL"
                    )

                    # -------------------------------------------------
                    # Select language
                    # -------------------------------------------------

                    if name_language == "AR":
                        full_name = name_ar or name_en or "-"
                        short_name = short_ar or short_en or full_name

                    elif name_language == "BOTH":
                        if name_en and name_ar and name_en != name_ar:
                            full_name = f"{name_en} / {name_ar}"
                        else:
                            full_name = name_en or name_ar or "-"

                        if short_en and short_ar and short_en != short_ar:
                            short_name = f"{short_en} / {short_ar}"
                        else:
                            short_name = short_en or short_ar or full_name

                    else:
                        full_name = name_en or name_ar or "-"
                        short_name = short_en or short_ar or full_name

                    # -------------------------------------------------
                    # Select full / short / full + short
                    # -------------------------------------------------

                    if name_display == "SHORT":
                        display_name = short_name

                    elif name_display == "FULL_SHORT":
                        # Do not produce:
                        # CBC (CBC)
                        # Complete Blood Count (Complete Blood Count)
                        if (
                            short_name
                            and full_name
                            and short_name.strip() != full_name.strip()
                        ):
                            display_name = (
                                f"{full_name} ({short_name})"
                            )
                        else:
                            display_name = full_name

                    else:
                        display_name = full_name

                    row.append(
                        p_en(
                            display_name,
                            table_style
                        )
                    )

                elif key == "test_code":
                    row.append(
                        p_en(
                            getattr(test, "code", "-"),
                            table_style
                        )
                    )

                elif key == "result":
                    row.append(
                        p_en(
                            result_value,
                            ParagraphStyle(
                                "ResultGrouped",
                                parent=table_style,
                                fontName="Helvetica-Bold",
                                fontSize=table_font_size + 1,
                                leading=table_font_size + 2,
                            )
                        )
                    )

                elif key == "unit":
                    row.append(
                        p_en(
                            getattr(test, "unit", None),
                            table_style
                        )
                    )

                elif key == "reference":
                    row.append(
                        p_en(
                            getattr(test, "reference_range", None),
                            table_style
                        )
                    )

                elif key == "flag":
                    row.append(
                        p_en(
                            getattr(item, "result_flag", None),
                            table_style
                        )
                    )

                elif key == "critical":
                    critical = (
                        getattr(item, "critical_status", None)
                        or "-"
                    )
                    row.append(
                        p_en(
                            critical,
                            table_style
                        )
                    )

                elif key == "sample":
                    row.append(
                        p_en(
                            getattr(test, "sample_type", None),
                            table_style
                        )
                    )

                elif key == "device":
                    row.append(
                        p_en(
                            getattr(test, "device", None),
                            table_style
                        )
                    )

                elif key == "reagent":
                    row.append(
                        p_en(
                            getattr(test, "reagent", None),
                            table_style
                        )
                    )

            result_data.append(row)

        # -----------------------------------------------------
        # -----------------------------------------------------
        # Dynamic column widths
        # -----------------------------------------------------
        # Column widths are controlled from LaboratoryReportSettings.
        # Values are stored in millimeters.
        # -----------------------------------------------------

        settings_widths_map = {
            "number": settings_obj.column_width_number,
            "test": settings_obj.column_width_test,
            "test_code": settings_obj.column_width_test_code,
            "result": settings_obj.column_width_result,
            "unit": settings_obj.column_width_unit,
            "reference": settings_obj.column_width_reference,
            "flag": settings_obj.column_width_flag,
            "critical": settings_obj.column_width_critical,
            "sample": settings_obj.column_width_sample,
            "device": settings_obj.column_width_device,
            "reagent": settings_obj.column_width_reagent,
        }

        raw_widths = []

        for key in column_keys:
            configured_width = settings_widths_map.get(key, 20)

            try:
                configured_width = float(configured_width)
            except (TypeError, ValueError):
                configured_width = 20.0

            # Prevent invalid widths from breaking ReportLab.
            if configured_width <= 0:
                configured_width = 20.0

            raw_widths.append(configured_width * mm)

        total_width = sum(raw_widths)

        # Automatic fitting to the printable page width.
        if settings_obj.auto_column_widths:
            if total_width > available_width:
                scale = available_width / total_width

                raw_widths = [
                    width * scale
                    for width in raw_widths
                ]

            elif total_width < available_width and raw_widths:
                extra = available_width - total_width
                raw_widths[-1] += extra

        results_table = Table(
            result_data,
            colWidths=raw_widths,
            repeatRows=1,
)

        table_commands = [
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                table_header,
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                table_text,
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.35,
                colors.HexColor("#cfd6dd"),
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE",
            ),
            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER",
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                3,
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                3,
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                4,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                4,
            ),
        ]

        for row_index, item in enumerate(
            department_items,
            start=1
        ):

            if row_index % 2 == 0:
                table_commands.append(
                    (
                        "BACKGROUND",
                        (0, row_index),
                        (-1, row_index),
                        colors.HexColor("#f8f9fa"),
                    )
                )

            if getattr(
                item,
                "critical_status",
                None
            ):

                try:
                    critical_index = column_keys.index(
                        "critical"
                    )

                    table_commands.extend([
                        (
                            "BACKGROUND",
                            (critical_index, row_index),
                            (critical_index, row_index),
                            colors.HexColor("#dc3545"),
                        ),
                        (
                            "TEXTCOLOR",
                            (critical_index, row_index),
                            (critical_index, row_index),
                            colors.white,
                        ),
                    ])

                except ValueError:
                    pass

        if not settings_obj.print_color:

            table_commands = [
                command
                for command in table_commands
                if not (
                    command[0] == "BACKGROUND"
                    and command[1][1] == 0
                )
            ]

            table_commands.append(
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#eeeeee"),
                )
            )

            table_commands.append(
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.black,
                )
            )

        results_table.setStyle(
            TableStyle(table_commands)
        )

        story.append(results_table)

    # ---------------------------------------------------------
    # Examiner notes
    # ---------------------------------------------------------

    if settings_obj.show_examiner_notes:

        notes = []

        for item in items:

            if item.examiner_notes:

                # Use the same configured test-name language
                # and display mode as the main laboratory report.

                test = item.test

                note_name_en = (
                    getattr(test, "name_en", None) or ""
                ).strip()

                note_name_ar = (
                    getattr(test, "name_ar", None) or ""
                ).strip()

                note_short_en = (
                    getattr(test, "short_name_en", None) or ""
                ).strip()

                note_short_ar = (
                    getattr(test, "short_name_ar", None) or ""
                ).strip()

                # Safe fallback for tests without short names.
                if not note_short_en:
                    note_short_en = note_name_en

                if not note_short_ar:
                    note_short_ar = note_name_ar

                note_language = getattr(
                    settings_obj,
                    "test_name_language",
                    "EN",
                )

                note_display = getattr(
                    settings_obj,
                    "test_name_display",
                    "FULL",
                )

                # Select language.
                if note_language == "AR":

                    note_full_name = (
                        note_name_ar
                        or note_name_en
                        or "-"
                    )

                    note_short_name = (
                        note_short_ar
                        or note_short_en
                        or note_full_name
                    )

                elif note_language == "BOTH":

                    if (
                        note_name_en
                        and note_name_ar
                        and note_name_en != note_name_ar
                    ):
                        note_full_name = (
                            f"{note_name_en} / {note_name_ar}"
                        )
                    else:
                        note_full_name = (
                            note_name_en
                            or note_name_ar
                            or "-"
                        )

                    if (
                        note_short_en
                        and note_short_ar
                        and note_short_en != note_short_ar
                    ):
                        note_short_name = (
                            f"{note_short_en} / {note_short_ar}"
                        )
                    else:
                        note_short_name = (
                            note_short_en
                            or note_short_ar
                            or note_full_name
                        )

                else:

                    note_full_name = (
                        note_name_en
                        or note_name_ar
                        or "-"
                    )

                    note_short_name = (
                        note_short_en
                        or note_short_ar
                        or note_full_name
                    )

                # Select FULL / SHORT / FULL_SHORT.
                if note_display == "SHORT":

                    note_test_name = note_short_name

                elif note_display == "FULL_SHORT":

                    if (
                        note_short_name
                        and note_full_name
                        and note_short_name.strip()
                        != note_full_name.strip()
                    ):
                        note_test_name = (
                            f"{note_full_name} "
                            f"({note_short_name})"
                        )
                    else:
                        note_test_name = note_full_name

                else:

                    note_test_name = note_full_name

                notes.append(
                    p_en(
                        f"{note_test_name}: "
                        f"{item.examiner_notes}",
                        body_en_style,
                    )
                )

    # Status
    # ---------------------------------------------------------

    story.append(Spacer(1, 4 * mm))

    status_text = str(
        getattr(order, "status", "")
    )

    if status_text in ("COMPLETED", "VERIFIED"):

        status_display = (
            "✓ Report Completed & Verified"
        )

        status_color = colors.HexColor(
            "#198754"
        )

    else:

        status_display = (
            f"Report Status: {status_text or '-'}"
        )

        status_color = colors.HexColor(
            "#fd7e14"
        )

    status_style = ParagraphStyle(
        "Status",
        parent=body_en_style,
        fontName="Helvetica-Bold",
        fontSize=9,
        alignment=TA_CENTER,
        textColor=status_color,
    )

    story.append(
        Paragraph(
            status_display,
            status_style
        )
    )

    # ---------------------------------------------------------
    # Signatures
    # ---------------------------------------------------------

    signature_data = []

    examiner_name = "-"

    verifier_name = "-"

    for item in items:

        if not examiner_name != "-":
            pass

        if (
            examiner_name == "-"
            and item.examiner
        ):

            examiner_name = (
                item.examiner.get_full_name()
                or item.examiner.username
            )

        if (
            verifier_name == "-"
            and item.verified_by
        ):

            verifier_name = (
                item.verified_by.get_full_name()
                or item.verified_by.username
            )

    if settings_obj.show_examiner_signature:

        signature_data.append([
            p_ar(settings_obj.examiner_signature_label),
            p_ar(examiner_name),
            "________________________",
        ])

    if settings_obj.show_verifier_signature:

        signature_data.append([
            p_ar(settings_obj.verifier_signature_label),
            p_ar(verifier_name),
            "________________________",
        ])

    if settings_obj.show_director_signature:

        signature_data.append([
            p_ar(settings_obj.director_signature_label),
            p_ar("-"),
            "________________________",
        ])

    if signature_data:

        story.append(Spacer(1, 8 * mm))

        sig_table = Table(
            [
                [
                    p_ar("التوقيع"),
                    p_ar("الاسم"),
                    p_ar("Signature"),
                ]
            ] + signature_data,
            colWidths=[
                available_width / 3,
                available_width / 3,
                available_width / 3,
            ],
        )

        sig_table.setStyle(
            TableStyle([
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.35,
                    colors.HexColor("#d5d9dd"),
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#f1f3f5"),
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ])
        )

        story.append(sig_table)

    # ---------------------------------------------------------
    # Footer
    # ---------------------------------------------------------

    footer_ar = str(
        settings_obj.report_footer or ""
    ).strip()

    footer_en = str(
        settings_obj.report_footer_en or ""
    ).strip()

    address = str(
        hospital_identity["address"] or ""
    ).strip()

    phone = str(
        hospital_identity["phone"] or ""
    ).strip()

    email = str(
        hospital_identity["email"] or ""
    ).strip()

    # ---------------------------------------------------------
    # Page callback
    # ---------------------------------------------------------

    def draw_page(canvas_obj, document_obj):

        canvas_obj.saveState()

        width, height = page_size

        # Background
        if settings_obj.print_color:
            canvas_obj.setFillColor(
                background_color
            )

            canvas_obj.rect(
                0,
                0,
                width,
                height,
                fill=1,
                stroke=0,
            )

        # Watermark
        if settings_obj.watermark_enabled:

            try:

                opacity = float(
                    settings_obj.watermark_opacity
                    or 0.08
                )

                opacity = max(
                    0,
                    min(1, opacity)
                )

                canvas_obj.setFillAlpha(
                    opacity
                )

            except Exception:

                pass

            canvas_obj.setFillColor(
                colors.HexColor("#999999")
            )

            canvas_obj.setFont(
                "Helvetica-Bold",
                55,
            )

            canvas_obj.translate(
                width / 2,
                height / 2,
            )

            canvas_obj.rotate(-35)

            canvas_obj.drawCentredString(
                0,
                0,
                str(
                    settings_obj.watermark_text
                    or "LABORATORY"
                )[:40],
            )

            canvas_obj.restoreState()
            canvas_obj.saveState()

        # Footer
        if settings_obj.show_footer:

            canvas_obj.setStrokeColor(
                colors.HexColor("#cccccc")
            )

            canvas_obj.line(
                margin_left,
                12 * mm,
                width - margin_right,
                12 * mm,
            )

            footer_lines = []

            if address:
                footer_lines.append(address)

            if phone:
                footer_lines.append(
                    f"Tel: {phone}"
                )

            if email:
                footer_lines.append(
                    f"Email: {email}"
                )

            if footer_lines:

                canvas_obj.setFont(
                    "Helvetica",
                    6.5,
                )

                canvas_obj.setFillColor(
                    colors.HexColor("#666666")
                )

                canvas_obj.drawCentredString(
                    width / 2,
                    8.5 * mm,
                    " | ".join(
                        footer_lines
                    )[:220],
                )

            if footer_ar:

                canvas_obj.setFont(
                    AR_FONT,
                    6.5,
                )

                canvas_obj.drawCentredString(
                    width / 2,
                    5.5 * mm,
                    ar(footer_ar)[:180],
                )

            if footer_en:

                canvas_obj.setFont(
                    "Helvetica",
                    6,
                )

                canvas_obj.drawCentredString(
                    width / 2,
                    3 * mm,
                    footer_en[:180],
                )

        # Page number
        if settings_obj.show_page_number:

            canvas_obj.setFont(
                "Helvetica",
                6.5,
            )

            canvas_obj.setFillColor(
                colors.HexColor("#666666")
            )

            canvas_obj.drawRightString(
                width - margin_right,
                5 * mm,
                f"Page {document_obj.page}",
            )

        # Print datetime
        if settings_obj.show_print_datetime:

            canvas_obj.setFont(
                "Helvetica",
                6,
            )

            canvas_obj.setFillColor(
                colors.HexColor("#777777")
            )

            canvas_obj.drawString(
                margin_left,
                5 * mm,
                timezone.localtime().strftime(
                    "%Y-%m-%d %H:%M"
                ),
            )

        canvas_obj.restoreState()

    # ---------------------------------------------------------
    # Build
    # ---------------------------------------------------------

    doc.build(
        story,
        onFirstPage=draw_page,
        onLaterPages=draw_page,
    )

    pdf = buffer.getvalue()

    buffer.close()

    response.write(pdf)

    create_laboratory_audit_log(
        request,
        "REPORT_PDF_GENERATED",
        order=order,
        description=(
            f"تم إنشاء PDF للتقرير "
            f"{filename_number}"
        ),
    )

    return response


def sync_laboratory_order_status(order):
    """
    مزامنة حالة LaboratoryOrder مع حالات عناصر الفحوصات التابعة له.

    الأولوية:
    COMPLETED  -> كل العناصر مكتملة
    PROCESSING -> يوجد عنصر قيد المعالجة
    COLLECTED -> يوجد عنصر مسحوب
    RECEIVED   -> يوجد عنصر مستلم
    REQUESTED  -> العناصر ما زالت مطلوبة
    CANCELLED  -> جميع العناصر ملغاة
    """

    items = list(
        order.items.values_list("status", flat=True)
    )

    if not items:
        return order.status

    active_statuses = [
        status for status in items
        if status != "CANCELLED"
    ]

    # جميع العناصر ملغاة
    if not active_statuses:
        new_status = "CANCELLED"

    # جميع العناصر مكتملة
    elif all(
        status == "COMPLETED"
        for status in active_statuses
    ):
        new_status = "COMPLETED"

    # يوجد عنصر قيد المعالجة
    elif any(
        status == "PROCESSING"
        for status in active_statuses
    ):
        new_status = "PROCESSING"

    # يوجد عنصر تم سحب عينته
    elif any(
        status == "COLLECTED"
        for status in active_statuses
    ):
        new_status = "COLLECTED"

    # يوجد عنصر تم استلامه
    elif any(
        status == "RECEIVED"
        for status in active_statuses
    ):
        new_status = "RECEIVED"

    # جميع العناصر ما زالت مطلوبة
    else:
        new_status = "REQUESTED"

    if order.status != new_status:
        order.status = new_status
        order.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

    return order.status


def sample_reception(request):
    """
    استقبال العينات وإدارة دورة العينة:

    REQUESTED -> RECEIVED -> COLLECTED
                    |
                    -> REJECTED -> RESAMPLE -> REQUESTED

    لا يتم حذف أي بيانات.
    """

    from django.db.models import Q, Count
    from .models import LaboratoryOrderItem

    if not lab_require_permission(
        request,
        "laboratory.sample.receive",
        "ليس لديك صلاحية استلام أو تسجيل العينات.",
    ):
        return redirect("laboratory:dashboard")

    user_department = get_user_lab_department(request.user)

    if not is_lab_manager(request.user) and not user_department:
        return lab_access_denied(
            request,
            "لا يوجد قسم مختبر مرتبط بحسابك."
        )

    # ==========================================================
    # POST ACTIONS
    # ==========================================================
    if request.method == "POST":

        item_id = request.POST.get(
            "item_id",
            ""
        ).strip()

        if not item_id.isdigit():
            messages.error(
                request,
                "رقم العينة غير صحيح."
            )
            return redirect("laboratory:sample_reception")

        try:
            item = (
                LaboratoryOrderItem.objects
                .select_related(
                    "order",
                    "order__patient",
                    "order__requesting_department",
                    "order__requesting_doctor",
                    "test",
                    "test__department",
                )
                .get(id=int(item_id))
            )
        except LaboratoryOrderItem.DoesNotExist:
            messages.error(
                request,
                "العينة غير موجودة."
            )
            return redirect("laboratory:sample_reception")

        # ------------------------------------------------------
        # صلاحيات القسم
        # ------------------------------------------------------
        if not is_lab_manager(request.user):
            if not user_can_access_order_item(
                request.user,
                item
            ):
                return lab_access_denied(
                    request,
                    "لا يمكنك التعامل مع عينة تابعة لقسم مختبر آخر."
                )

        action = request.POST.get(
            "action",
            "receive"
        ).strip().lower()

        # ======================================================
        # 1. استلام العينة
        # ======================================================
        if action == "receive":

            if item.status != "REQUESTED":
                messages.warning(
                    request,
                    "لا يمكن استلام هذه العينة. "
                    f"الحالة الحالية: {item.status}"
                )
                return redirect("laboratory:sample_reception")

            item.status = "RECEIVED"

            item.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )

            sync_laboratory_order_status(item.order)

            messages.success(
                request,
                f"تم استلام عينة الطلب "
                f"{item.order.order_number} بنجاح."
            )

        # ======================================================
        # 2. سحب العينة
        # ======================================================
        elif action == "collect":

            if item.status != "RECEIVED":
                messages.warning(
                    request,
                    "يجب استلام العينة أولاً قبل تسجيل سحبها. "
                    f"الحالة الحالية: {item.status}"
                )
                return redirect("laboratory:sample_reception")

            # إنشاء رقم عينة
            if not item.sample_id:
                suffix = max(
                    1,
                    int(item.resample_count or 0) + 1
                )

                item.sample_id = (
                    f"{item.order.order_number}-"
                    f"{item.id:03d}-S{suffix:02d}"
                )

            item.sample_collected_at = timezone.now()
            item.status = "COLLECTED"

            item.save(
                update_fields=[
                    "sample_id",
                    "sample_collected_at",
                    "status",
                    "updated_at",
                ]
            )

            sync_laboratory_order_status(item.order)

            messages.success(
                request,
                "تم سحب العينة بنجاح. "
                f"Sample ID: {item.sample_id}"
            )

        # ======================================================
        # 3. رفض العينة
        # ======================================================
        elif action == "reject":

            if item.status not in {
                "REQUESTED",
                "RECEIVED",
            }:
                messages.warning(
                    request,
                    "لا يمكن رفض العينة في حالتها الحالية: "
                    f"{item.status}"
                )
                return redirect("laboratory:sample_reception")

            rejection_reason = request.POST.get(
                "rejection_reason",
                ""
            ).strip()

            if not rejection_reason:
                messages.error(
                    request,
                    "يجب إدخال سبب رفض العينة."
                )
                return redirect("laboratory:sample_reception")

            item.status = "REJECTED"
            item.rejection_reason = rejection_reason
            item.rejected_at = timezone.now()
            item.rejected_by = request.user

            item.save(
                update_fields=[
                    "status",
                    "rejection_reason",
                    "rejected_at",
                    "rejected_by",
                    "updated_at",
                ]
            )

            sync_laboratory_order_status(item.order)

            messages.success(
                request,
                f"تم رفض العينة {item.order.order_number} "
                "وتسجيل سبب الرفض."
            )

        # ======================================================
        # 4. إعادة السحب
        # ======================================================
        elif action == "resample":

            if item.status != "REJECTED":
                messages.warning(
                    request,
                    "إعادة السحب متاحة فقط للعينة المرفوضة."
                )
                return redirect("laboratory:sample_reception")

            item.resample_count = (
                int(item.resample_count or 0) + 1
            )

            # تبدأ دورة السحب الجديدة من REQUESTED
            item.status = "REQUESTED"

            # لا نحذف سبب الرفض السابق
            # حتى يبقى آخر سبب رفض ظاهرًا في السجل الحالي.

            item.sample_id = ""
            item.sample_collected_at = None

            item.save(
                update_fields=[
                    "status",
                    "resample_count",
                    "sample_id",
                    "sample_collected_at",
                    "updated_at",
                ]
            )

            sync_laboratory_order_status(item.order)

            messages.success(
                request,
                "تمت إعادة العينة إلى قائمة العينات المطلوبة "
                "لإعادة السحب."
            )

        else:

            messages.error(
                request,
                "إجراء غير معروف."
            )

        return redirect(
            "laboratory:sample_reception"
        )

    # ==========================================================
    # GET / قائمة العينات
    # ==========================================================

    items = (
        LaboratoryOrderItem.objects
        .select_related(
            "order",
            "order__patient",
            "order__requesting_department",
            "order__requesting_doctor",
            "test",
            "test__department",
            "rejected_by",
        )
        .filter(
            status__in=[
                "REQUESTED",
                "RECEIVED",
                "REJECTED",
            ]
        )
    )

    # ----------------------------------------------------------
    # تقييد النتائج حسب قسم المستخدم
    # ----------------------------------------------------------
    if not is_lab_manager(request.user):

        if user_department.code != "LAB":

            items = items.filter(
                test__department_id=user_department.id
            )

    # ----------------------------------------------------------
    # البحث
    # ----------------------------------------------------------
    query = request.GET.get(
        "q",
        ""
    ).strip()

    if query:

        items = items.filter(
            Q(
                order__order_number__icontains=query
            )
            |
            Q(
                order__patient__full_name__icontains=query
            )
            |
            Q(
                order__patient__patient_number__icontains=query
            )
            |
            Q(
                sample_id__icontains=query
            )
            |
            Q(
                test__name_en__icontains=query
            )
            |
            Q(
                test__name_ar__icontains=query
            )
            |
            Q(
                rejection_reason__icontains=query
            )
        ).distinct()

    # ----------------------------------------------------------
    # فلتر الحالة
    # ----------------------------------------------------------
    status_filter = request.GET.get(
        "status",
        ""
    ).strip()

    if status_filter in {
        "REQUESTED",
        "RECEIVED",
        "REJECTED",
    }:

        items = items.filter(
            status=status_filter
        )

    # ----------------------------------------------------------
    # فلتر الأولوية
    # ----------------------------------------------------------
    priority_filter = request.GET.get(
        "priority",
        ""
    ).strip()

    if priority_filter in {
        "NORMAL",
        "URGENT",
        "STAT",
    }:

        items = items.filter(
            order__priority=priority_filter
        )

    items = items.order_by(
        "order__priority",
        "order__requested_at",
    )

    # ==========================================================
    # الإحصائيات
    # ==========================================================

    stats = (
        LaboratoryOrderItem.objects
    )

    if not is_lab_manager(request.user):

        if user_department.code != "LAB":

            stats = stats.filter(
                test__department_id=user_department.id
            )

    requested_count = stats.filter(
        status="REQUESTED"
    ).count()

    received_count = stats.filter(
        status="RECEIVED"
    ).count()

    rejected_count = stats.filter(
        status="REJECTED"
    ).count()

    collected_count = stats.filter(
        status="COLLECTED"
    ).count()

    stat_count = stats.filter(
        status__in=[
            "REQUESTED",
            "RECEIVED",
            "REJECTED",
        ],
        order__priority="STAT"
    ).count()

    urgent_count = stats.filter(
        status__in=[
            "REQUESTED",
            "RECEIVED",
            "REJECTED",
        ],
        order__priority="URGENT"
    ).count()

    resample_count = stats.filter(
        resample_count__gt=0
    ).count()

    return render(
        request,
        "laboratory/sample_reception.html",
        {
            "items": items,
            "query": query,
            "status_filter": status_filter,
            "priority_filter": priority_filter,

            "requested_count": requested_count,
            "received_count": received_count,
            "rejected_count": rejected_count,
            "collected_count": collected_count,
            "stat_count": stat_count,
            "urgent_count": urgent_count,
            "resample_count": resample_count,
        }
    )

@login_required
def test_list(request):
    if not lab_require_permission(
        request,
        "laboratory.tests.view",
        "ليس لديك صلاحية عرض الفحوصات.",
    ):
        return redirect("laboratory:dashboard")

    from .models import LaboratoryTest

    tests = LaboratoryTest.objects.select_related("department").all()

    # ========================================================
    # Department access control
    # ========================================================
    tests = get_lab_user_tests(request.user, tests)


    q = request.GET.get("q", "").strip()
    department_id = request.GET.get("department", "").strip()
    active = request.GET.get("active", "").strip()

    if q:
        tests = tests.filter(
            models.Q(code__icontains=q) |
            models.Q(name_en__icontains=q) |
            models.Q(name_ar__icontains=q)
        )

    if department_id:
        tests = tests.filter(department_id=department_id)

    if active == "1":
        tests = tests.filter(is_active=True)
    elif active == "0":
        tests = tests.filter(is_active=False)

    departments = Department.objects.filter(
        is_active=True
    ).order_by("name_ar")

    return render(
        request,
        "laboratory/test_list.html",
        {
            "tests": tests,
            "departments": departments,
            "q": q,
            "selected_department": department_id,
            "selected_active": active,
        }
    )


@login_required
def test_create(request):
    if not lab_require_permission(
        request,
        "laboratory.tests.create",
        "ليس لديك صلاحية إضافة فحص مخبري.",
    ):
        return redirect("laboratory:dashboard")

    from .models import LaboratoryTest

    # ========================================================
    # Department access control
    # ========================================================
    user_department = get_user_lab_department(request.user)

    if (
        not is_lab_manager(request.user)
        and not user_department
    ):
        return lab_access_denied(
            request,
            "لا يوجد قسم مختبر مرتبط بحسابك."
        )

    if request.method == "POST":
        code = request.POST.get("code", "").strip()
        name_en = request.POST.get("name_en", "").strip()
        name_ar = request.POST.get("name_ar", "").strip()
        short_name_en = request.POST.get("short_name_en", "").strip()
        short_name_ar = request.POST.get("short_name_ar", "").strip()
        department_id = request.POST.get("department") or None

        # Non-central laboratory users can only create tests
        # inside their own laboratory department.
        if (
            not is_lab_manager(request.user)
            and user_department
            and user_department.code != "LAB"
        ):
            department_id = user_department.id

        sample_type = request.POST.get("sample_type", "SERUM")
        unit = request.POST.get("unit", "").strip()
        device = request.POST.get("device", "").strip()
        reagent = request.POST.get("reagent", "").strip()
        reference_range = request.POST.get("reference_range", "").strip()
        price = request.POST.get("price", "0").strip() or "0"
        is_active = request.POST.get("is_active") == "on"

        if not code or not name_en:
            messages.error(
                request,
                "Test Code و English Test Name مطلوبان."
            )
        elif LaboratoryTest.objects.filter(code=code).exists():
            messages.error(
                request,
                "كود الفحص موجود مسبقًا."
            )
        else:
            LaboratoryTest.objects.create(
                code=code,
                name_en=name_en,
                name_ar=name_ar,
                short_name_en=short_name_en,
                short_name_ar=short_name_ar,
                department_id=department_id,
                sample_type=sample_type,
                unit=unit,
                device=device,
                reagent=reagent,
                reference_range=reference_range,
                price=price,
                is_active=is_active,
            )

            messages.success(
                request,
                "تمت إضافة الفحص بنجاح."
            )

            return redirect("laboratory:test_list")

    departments = Department.objects.filter(
        is_active=True
    ).order_by("name_ar")

    if (
        not is_lab_manager(request.user)
        and user_department
        and user_department.code != "LAB"
    ):
        departments = departments.filter(
            id=user_department.id
        )

    return render(
        request,
        "laboratory/test_form.html",
        {
            "departments": departments,
            "test": None,
            "sample_types": LaboratoryTest.SAMPLE_TYPES,
        }
    )


@login_required
def test_edit(request, test_id):
    if not lab_require_permission(
        request,
        "laboratory.tests.edit",
        "ليس لديك صلاحية تعديل الفحوصات.",
    ):
        return redirect("laboratory:dashboard")

    from .models import LaboratoryTest

    test = get_object_or_404(
        LaboratoryTest,
        id=test_id
    )


    # ========================================================
    # Department access control
    # ========================================================
    if not user_can_access_test(request.user, test):
        return lab_access_denied(
            request,
            "لا يمكنك تعديل فحص تابع لقسم مختبر آخر."
        )

    if request.method == "POST":
        code = request.POST.get("code", "").strip()
        name_en = request.POST.get("name_en", "").strip()
        short_name_en = request.POST.get("short_name_en", "").strip()
        short_name_ar = request.POST.get("short_name_ar", "").strip()

        if not code or not name_en:
            messages.error(
                request,
                "Test Code و English Test Name مطلوبان."
            )
        elif LaboratoryTest.objects.filter(
            code=code
        ).exclude(id=test.id).exists():
            messages.error(
                request,
                "كود الفحص مستخدم في فحص آخر."
            )
        else:
            test.code = code
            test.name_en = name_en
            test.name_ar = request.POST.get("name_ar", "").strip()
            test.short_name_en = short_name_en
            test.short_name_ar = short_name_ar
            test.department_id = request.POST.get("department") or None

            # جميع المستخدمين الذين يملكون صلاحية edit
            # يستطيعون تعديل بيانات الفحص.
            test.sample_type = request.POST.get(
                "sample_type",
                "SERUM"
            )
            test.unit = request.POST.get("unit", "").strip()
            test.device = request.POST.get("device", "").strip()
            test.reagent = request.POST.get("reagent", "").strip()
            test.reference_range = request.POST.get(
                "reference_range",
                ""
            ).strip()
            test.price = request.POST.get(
                "price",
                "0"
            ).strip() or "0"
            test.is_active = request.POST.get("is_active") == "on"

            # مستخدم القسم لا يستطيع نقل الفحص إلى قسم آخر.
            user_department = get_user_lab_department(request.user)
            if (
                not is_lab_manager(request.user)
                and user_department
                and user_department.code != "LAB"
            ):
                test.department_id = user_department.id

            test.save()

            messages.success(
                request,
                "تم تعديل الفحص بنجاح."
            )

            return redirect("laboratory:test_list")

    departments = Department.objects.filter(
        is_active=True
    ).order_by("name_ar")

    user_department = get_user_lab_department(request.user)

    if (
        not is_lab_manager(request.user)
        and user_department
        and user_department.code != "LAB"
    ):
        departments = departments.filter(
            id=user_department.id
        )

    return render(
        request,
        "laboratory/test_form.html",
        {
            "departments": departments,
            "test": test,
            "sample_types": LaboratoryTest.SAMPLE_TYPES,
        }
    )


@login_required
def test_toggle(request, test_id):
    if not lab_require_permission(
        request,
        "laboratory.tests.toggle",
        "ليس لديك صلاحية تفعيل أو تعطيل الفحوصات.",
    ):
        return redirect("laboratory:dashboard")

    from .models import LaboratoryTest

    test = get_object_or_404(
        LaboratoryTest,
        id=test_id
    )


    if not user_can_access_test(request.user, test):
        return lab_access_denied(
            request,
            "لا يمكنك تغيير حالة فحص تابع لقسم مختبر آخر."
        )

    if request.method == "POST":
        test.is_active = not test.is_active
        test.save(update_fields=["is_active", "updated_at"])

        if test.is_active:
            messages.success(
                request,
                f"تم تفعيل الفحص: {test.name_en}"
            )
        else:
            messages.warning(
                request,
                f"تم تعطيل الفحص: {test.name_en}"
            )

    return redirect("laboratory:test_list")


@login_required
def test_delete(request, test_id):
    if not lab_require_permission(
        request,
        "laboratory.tests.delete",
        "ليس لديك صلاحية حذف الفحوصات.",
    ):
        return redirect("laboratory:dashboard")

    from .models import LaboratoryTest

    test = get_object_or_404(
        LaboratoryTest,
        id=test_id
    )


    if not user_can_access_test(request.user, test):
        return lab_access_denied(
            request,
            "لا يمكنك حذف فحص تابع لقسم مختبر آخر."
        )

    if request.method == "POST":
        name = test.name_en
        test.delete()

        messages.success(
            request,
            f"تم حذف الفحص: {name}"
        )

    return redirect("laboratory:test_list")

# ============================================================
# Laboratory Devices / Reagents / Inventory Management
# ============================================================

from datetime import date, timedelta
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404
from .models_inventory import (
    LaboratoryDevice,
    LaboratoryReagent,
    LaboratoryReagentStock,
    LaboratoryStockMovement,
)


@login_required
def device_list(request):
    if not lab_require_permission(request, "laboratory.devices.view"):
        return redirect("laboratory:dashboard")

    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()

    devices = LaboratoryDevice.objects.select_related(
        "department"
    ).order_by("name")

    # تقييد عرض الأجهزة حسب قسم المستخدم.
    devices = get_lab_user_devices(request.user, devices)

    if q:
        devices = devices.filter(
            Q(name__icontains=q)
            | Q(manufacturer__icontains=q)
            | Q(model__icontains=q)
            | Q(serial_number__icontains=q)
        )

    if status:
        devices = devices.filter(status=status)

    return render(
        request,
        "laboratory/device_list.html",
        {
            "devices": devices,
            "q": q,
            "status": status,
            "status_choices": LaboratoryDevice.STATUS_CHOICES,
        },
    )


@login_required
def device_create(request):
    if not lab_require_permission(request, "laboratory.devices.create"):
        return redirect("laboratory:dashboard")

    departments = Department.objects.filter(
        is_active=True
    ).order_by("name_en")

    user_department = get_user_lab_department(request.user)

    if (
        not is_lab_manager(request.user)
        and user_department
        and user_department.code != "LAB"
    ):
        departments = departments.filter(
            id=user_department.id
        )

    if (
        not is_lab_manager(request.user)
        and not user_department
    ):
        return lab_access_denied(
            request,
            "لا يوجد قسم مختبر مرتبط بحساب المستخدم."
        )

    if request.method == "POST":
        name = request.POST.get("name", "").strip()

        if not name:
            messages.error(request, "يجب إدخال اسم الجهاز.")
        else:
            department_id = request.POST.get("department") or None

            # مستخدم القسم لا يستطيع إنشاء جهاز في قسم آخر.
            if (
                not is_lab_manager(request.user)
                and user_department
                and user_department.code != "LAB"
            ):
                department_id = user_department.id

            LaboratoryDevice.objects.create(
                name=name,
                manufacturer=request.POST.get("manufacturer", "").strip(),
                model=request.POST.get("model", "").strip(),
                serial_number=request.POST.get("serial_number", "").strip(),
                department_id=department_id,
                status=request.POST.get("status") or "ACTIVE",
                notes=request.POST.get("notes", "").strip(),
                is_active=request.POST.get("is_active") == "on",
            )
            messages.success(request, "تمت إضافة الجهاز بنجاح.")
            return redirect("laboratory:device_list")

    return render(
        request,
        "laboratory/device_form.html",
        {
            "departments": departments,
            "status_choices": LaboratoryDevice.STATUS_CHOICES,
            "title": "إضافة جهاز مختبر",
        },
    )


@login_required
def device_edit(request, device_id):
    if not lab_require_permission(request, "laboratory.devices.edit"):
        return redirect("laboratory:dashboard")

    device = get_object_or_404(
        LaboratoryDevice.objects.select_related("department"),
        pk=device_id,
    )

    # حماية نطاق القسم.
    if not is_lab_manager(request.user):
        user_department = get_user_lab_department(request.user)

        if not user_department:
            return lab_access_denied(
                request,
                "لا يوجد قسم مختبر مرتبط بحساب المستخدم."
            )

        if (
            user_department.code != "LAB"
            and device.department_id != user_department.id
        ):
            return lab_access_denied(
                request,
                "لا يمكنك تعديل جهاز تابع لقسم مختبر آخر."
            )

    departments = Department.objects.filter(
        is_active=True
    ).order_by("name_en")

    user_department = get_user_lab_department(request.user)

    if (
        not is_lab_manager(request.user)
        and user_department
        and user_department.code != "LAB"
    ):
        departments = departments.filter(
            id=user_department.id
        )

    if request.method == "POST":
        device.name = request.POST.get("name", "").strip()
        device.manufacturer = request.POST.get("manufacturer", "").strip()
        device.model = request.POST.get("model", "").strip()
        device.serial_number = request.POST.get("serial_number", "").strip()
        department_id = request.POST.get("department") or None

        # مستخدم القسم لا يستطيع نقل الجهاز إلى قسم آخر.
        if (
            not is_lab_manager(request.user)
            and user_department
            and user_department.code != "LAB"
        ):
            department_id = user_department.id

        device.department_id = department_id
        device.status = request.POST.get("status") or "ACTIVE"
        device.notes = request.POST.get("notes", "").strip()
        device.is_active = request.POST.get("is_active") == "on"
        device.save()

        messages.success(request, "تم تحديث بيانات الجهاز.")
        return redirect("laboratory:device_list")

    return render(
        request,
        "laboratory/device_form.html",
        {
            "device": device,
            "departments": departments,
            "status_choices": LaboratoryDevice.STATUS_CHOICES,
            "title": "تعديل جهاز مختبر",
        },
    )


@login_required
def device_toggle(request, device_id):
    if not lab_require_permission(request, "laboratory.devices.toggle"):
        return redirect("laboratory:dashboard")

    device = get_object_or_404(
        LaboratoryDevice.objects.select_related("department"),
        pk=device_id,
    )

    if not is_lab_manager(request.user):
        user_department = get_user_lab_department(request.user)

        if not user_department:
            return lab_access_denied(
                request,
                "لا يوجد قسم مختبر مرتبط بحساب المستخدم."
            )

        if (
            user_department.code != "LAB"
            and device.department_id != user_department.id
        ):
            return lab_access_denied(
                request,
                "لا يمكنك تغيير حالة جهاز تابع لقسم مختبر آخر."
            )

    device.is_active = not device.is_active
    device.save(update_fields=["is_active", "updated_at"])

    messages.success(
        request,
        "تم تغيير حالة الجهاز."
    )

    return redirect("laboratory:device_list")


def get_lab_user_reagents(user, queryset=None):
    """
    تقييد كواشف المختبر حسب قسم المستخدم.

    المدير ومدير المستشفى والمستخدم المركزي LAB:
    يستطيعون الوصول إلى جميع الكواشف.

    مستخدم القسم:
    يستطيع الوصول إلى الكاشف إذا كان:
    1. الجهاز التابع للكاشف في قسمه.
    أو
    2. أحد الفحوصات المرتبطة بالكاشف في قسمه.

    الكاشف الذي لا يرتبط بجهاز أو فحص:
    لا يظهر لمستخدم القسم العادي.
    """
    if queryset is None:
        queryset = LaboratoryReagent.objects.all()

    if is_lab_manager(user):
        return queryset

    department = get_user_lab_department(user)

    if not department:
        return queryset.none()

    if department.code == "LAB":
        return queryset

    return queryset.filter(
        models.Q(device__department_id=department.id)
        | models.Q(tests__department_id=department.id)
    ).distinct()


def _get_lab_user_devices_queryset(user):
    """
    الأجهزة التي يسمح للمستخدم باختيارها عند إنشاء/تعديل كاشف.
    """
    devices = LaboratoryDevice.objects.filter(
        is_active=True
    ).order_by("name")

    return get_lab_user_devices(user, devices)


def _get_lab_user_tests_queryset(user):
    """
    الفحوصات التي يسمح للمستخدم بربطها بالكاشف.
    """
    tests = LaboratoryTest.objects.filter(
        is_active=True
    ).order_by("name_en")

    return get_lab_user_tests(user, tests)


@login_required
def reagent_list(request):
    if not lab_require_permission(
        request,
        "laboratory.reagents.view",
        "ليس لديك صلاحية عرض الكواشف.",
    ):
        return redirect("laboratory:dashboard")

    q = request.GET.get("q", "").strip()

    reagents = LaboratoryReagent.objects.select_related(
        "device",
        "device__department",
    ).prefetch_related(
        "tests",
        "tests__department",
    ).order_by("name")

    # تقييد عرض الكواشف حسب قسم المستخدم.
    reagents = get_lab_user_reagents(request.user, reagents)

    if q:
        reagents = reagents.filter(
            Q(name__icontains=q)
            | Q(manufacturer__icontains=q)
            | Q(catalog_number__icontains=q)
        )

    return render(
        request,
        "laboratory/reagent_list.html",
        {
            "reagents": reagents,
            "q": q,
        },
    )


@login_required
def reagent_create(request):
    if not lab_require_permission(
        request,
        "laboratory.reagents.create",
        "ليس لديك صلاحية إضافة الكواشف.",
    ):
        return redirect("laboratory:dashboard")

    devices = _get_lab_user_devices_queryset(request.user)
    tests = _get_lab_user_tests_queryset(request.user)

    user_department = get_user_lab_department(request.user)

    if (
        not is_lab_manager(request.user)
        and not user_department
    ):
        return lab_access_denied(
            request,
            "لا يوجد قسم مختبر مرتبط بحساب المستخدم."
        )

    if request.method == "POST":
        name = request.POST.get("name", "").strip()

        if not name:
            messages.error(request, "يجب إدخال اسم الكاشف.")
        else:
            device_id = request.POST.get("device") or None

            # التحقق من أن الجهاز المختار ضمن نطاق المستخدم.
            device = None

            if device_id:
                device = devices.filter(
                    pk=device_id
                ).first()

                if device is None:
                    return lab_access_denied(
                        request,
                        "لا يمكنك ربط الكاشف بجهاز تابع لقسم مختبر آخر."
                    )

            selected_test_ids = request.POST.getlist("tests")

            # التحقق من أن جميع الفحوصات المختارة مسموح بها.
            allowed_test_ids = set(
                tests.filter(
                    id__in=selected_test_ids
                ).values_list("id", flat=True)
            )

            invalid_test_ids = [
                test_id
                for test_id in selected_test_ids
                if str(test_id) not in {
                    str(x) for x in allowed_test_ids
                }
            ]

            if invalid_test_ids:
                return lab_access_denied(
                    request,
                    "لا يمكنك ربط الكاشف بفحص تابع لقسم مختبر آخر."
                )

            reagent = LaboratoryReagent.objects.create(
                name=name,
                manufacturer=request.POST.get(
                    "manufacturer",
                    ""
                ).strip(),
                catalog_number=request.POST.get(
                    "catalog_number",
                    ""
                ).strip(),
                device=device,
                unit=request.POST.get(
                    "unit",
                    ""
                ).strip(),
                notes=request.POST.get(
                    "notes",
                    ""
                ).strip(),
                is_active=request.POST.get(
                    "is_active"
                ) == "on",
            )

            reagent.tests.set(
                allowed_test_ids
            )

            messages.success(
                request,
                "تمت إضافة الكاشف بنجاح."
            )

            return redirect(
                "laboratory:reagent_list"
            )

    return render(
        request,
        "laboratory/reagent_form.html",
        {
            "devices": devices,
            "tests": tests,
            "title": "إضافة كاشف",
        },
    )


@login_required
def reagent_edit(request, reagent_id):
    if not lab_require_permission(
        request,
        "laboratory.reagents.edit",
        "ليس لديك صلاحية تعديل الكواشف.",
    ):
        return redirect("laboratory:dashboard")

    reagent = get_object_or_404(
        LaboratoryReagent.objects.select_related(
            "device",
            "device__department",
        ),
        pk=reagent_id,
    )

    # حماية نطاق القسم للكاشف نفسه.
    if not is_lab_manager(request.user):
        if not get_lab_user_reagents(
            request.user,
            LaboratoryReagent.objects.filter(pk=reagent.pk)
        ).exists():
            return lab_access_denied(
                request,
                "لا يمكنك تعديل كاشف تابع لقسم مختبر آخر."
            )

    devices = _get_lab_user_devices_queryset(request.user)
    tests = _get_lab_user_tests_queryset(request.user)

    if request.method == "POST":
        name = request.POST.get(
            "name",
            ""
        ).strip()

        if not name:
            messages.error(
                request,
                "يجب إدخال اسم الكاشف."
            )
        else:
            device_id = request.POST.get(
                "device"
            ) or None

            device = None

            if device_id:
                device = devices.filter(
                    pk=device_id
                ).first()

                if device is None:
                    return lab_access_denied(
                        request,
                        "لا يمكنك ربط الكاشف بجهاز تابع لقسم مختبر آخر."
                    )

            selected_test_ids = request.POST.getlist(
                "tests"
            )

            allowed_test_ids = set(
                tests.filter(
                    id__in=selected_test_ids
                ).values_list(
                    "id",
                    flat=True
                )
            )

            allowed_test_id_strings = {
                str(x)
                for x in allowed_test_ids
            }

            invalid_test_ids = [
                test_id
                for test_id in selected_test_ids
                if str(test_id) not in allowed_test_id_strings
            ]

            if invalid_test_ids:
                return lab_access_denied(
                    request,
                    "لا يمكنك ربط الكاشف بفحص تابع لقسم مختبر آخر."
                )

            reagent.name = name
            reagent.manufacturer = request.POST.get(
                "manufacturer",
                ""
            ).strip()
            reagent.catalog_number = request.POST.get(
                "catalog_number",
                ""
            ).strip()
            reagent.device = device
            reagent.unit = request.POST.get(
                "unit",
                ""
            ).strip()
            reagent.notes = request.POST.get(
                "notes",
                ""
            ).strip()
            reagent.is_active = request.POST.get(
                "is_active"
            ) == "on"

            reagent.save()

            reagent.tests.set(
                allowed_test_ids
            )

            messages.success(
                request,
                "تم تحديث بيانات الكاشف."
            )

            return redirect(
                "laboratory:reagent_list"
            )

    return render(
        request,
        "laboratory/reagent_form.html",
        {
            "reagent": reagent,
            "devices": devices,
            "tests": tests,
            "title": "تعديل كاشف",
        },
    )


@login_required
def reagent_toggle(request, reagent_id):
    if not lab_require_permission(
        request,
        "laboratory.reagents.toggle",
        "ليس لديك صلاحية تفعيل أو تعطيل الكواشف.",
    ):
        return redirect("laboratory:dashboard")

    reagent = get_object_or_404(
        LaboratoryReagent.objects.select_related(
            "device",
            "device__department",
        ),
        pk=reagent_id,
    )

    # حماية نطاق القسم.
    if not is_lab_manager(request.user):
        if not get_lab_user_reagents(
            request.user,
            LaboratoryReagent.objects.filter(pk=reagent.pk)
        ).exists():
            return lab_access_denied(
                request,
                "لا يمكنك تغيير حالة كاشف تابع لقسم مختبر آخر."
            )

    reagent.is_active = not reagent.is_active

    reagent.save(
        update_fields=[
            "is_active",
            "updated_at",
        ]
    )

    messages.success(
        request,
        "تم تغيير حالة الكاشف."
    )

    return redirect(
        "laboratory:reagent_list"
    )


def get_lab_user_stocks(user, queryset=None):
    """
    تقييد مخزون المختبر حسب قسم المستخدم.

    المدير/مدير المستشفى والمستخدم المركزي LAB:
    يستطيعون الوصول إلى كامل المخزون.

    مستخدم القسم:
    يستطيع الوصول فقط إلى مخزون الكواشف التابعة
    لقسمه، اعتماداً على علاقة الكاشف بالجهاز أو الفحص.
    """
    if queryset is None:
        queryset = LaboratoryReagentStock.objects.all()

    if is_lab_manager(user):
        return queryset

    department = get_user_lab_department(user)

    if not department:
        return queryset.none()

    if department.code == "LAB":
        return queryset

    return queryset.filter(
        models.Q(
            reagent__device__department_id=department.id
        )
        |
        models.Q(
            reagent__tests__department_id=department.id
        )
    ).distinct()


@login_required
def inventory_dashboard(request):
    if not lab_require_permission(
        request,
        "laboratory.inventory.view",
        "ليس لديك صلاحية عرض مخزون المختبر.",
    ):
        return redirect("laboratory:dashboard")

    stocks = LaboratoryReagentStock.objects.select_related(
        "reagent",
        "reagent__device",
        "reagent__device__department",
    ).prefetch_related(
        "reagent__tests",
        "reagent__tests__department",
    ).order_by(
        "expiry_date",
        "reagent__name",
    )

    # تقييد المخزون حسب قسم المستخدم.
    stocks = get_lab_user_stocks(
        request.user,
        stocks,
    )

    today = date.today()
    near_expiry_date = today + timedelta(days=30)

    low_stock = stocks.filter(
        quantity__lte=models.F("minimum_stock")
    )

    expired = stocks.filter(
        expiry_date__lt=today
    )

    near_expiry = stocks.filter(
        expiry_date__gte=today,
        expiry_date__lte=near_expiry_date,
    )

    return render(
        request,
        "laboratory/inventory_dashboard.html",
        {
            "stocks": stocks,
            "low_stock": low_stock,
            "expired": expired,
            "near_expiry": near_expiry,
            "today": today,
        },
    )


@login_required
def stock_create(request):
    if not lab_require_permission(
        request,
        "laboratory.inventory.create",
        "ليس لديك صلاحية إضافة مخزون المختبر.",
    ):
        return redirect("laboratory:dashboard")

    # المستخدم لا يرى إلا الكواشف المسموح له بإدارتها.
    reagents = LaboratoryReagent.objects.filter(
        is_active=True
    ).order_by("name")

    reagents = get_lab_user_reagents(
        request.user,
        reagents,
    )

    user_department = get_user_lab_department(request.user)

    if (
        not is_lab_manager(request.user)
        and not user_department
    ):
        return lab_access_denied(
            request,
            "لا يوجد قسم مختبر مرتبط بحساب المستخدم."
        )

    if request.method == "POST":
        reagent_id = request.POST.get("reagent")
        lot_number = request.POST.get(
            "lot_number",
            ""
        ).strip()
        expiry_date = request.POST.get("expiry_date")
        quantity = request.POST.get("quantity") or 0
        minimum_stock = request.POST.get(
            "minimum_stock"
        ) or 0

        if (
            not reagent_id
            or not lot_number
            or not expiry_date
        ):
            messages.error(
                request,
                "الكاشف ورقم Lot وتاريخ الانتهاء حقول مطلوبة."
            )
        else:
            # التحقق من صلاحية الكاشف قبل إنشاء المخزون.
            reagent = reagents.filter(
                pk=reagent_id
            ).first()

            if reagent is None:
                return lab_access_denied(
                    request,
                    "لا يمكنك إضافة مخزون لكاشف تابع لقسم مختبر آخر."
                )

            stock = LaboratoryReagentStock.objects.create(
                reagent=reagent,
                lot_number=lot_number,
                expiry_date=expiry_date,
                quantity=quantity,
                minimum_stock=minimum_stock,
                supplier=request.POST.get(
                    "supplier",
                    ""
                ).strip(),
                purchase_price=request.POST.get(
                    "purchase_price"
                ) or 0,
                notes=request.POST.get(
                    "notes",
                    ""
                ).strip(),
            )

            if quantity and float(quantity) > 0:
                LaboratoryStockMovement.objects.create(
                    stock=stock,
                    movement_type="IN",
                    quantity=quantity,
                    reference="Initial Stock",
                    performed_by=request.user,
                    notes="Initial stock entry",
                )

            messages.success(
                request,
                "تمت إضافة دفعة المخزون بنجاح."
            )

            return redirect(
                "laboratory:inventory_dashboard"
            )

    return render(
        request,
        "laboratory/stock_form.html",
        {
            "reagents": reagents,
            "title": "إضافة مخزون كاشف",
        },
    )


@login_required
def stock_movement(request, stock_id):
    if not lab_require_permission(
        request,
        "laboratory.inventory.movement",
        "ليس لديك صلاحية تنفيذ حركات مخزون المختبر.",
    ):
        return redirect("laboratory:dashboard")

    stock = get_object_or_404(
        LaboratoryReagentStock.objects.select_related(
            "reagent",
            "reagent__device",
            "reagent__device__department",
        ).prefetch_related(
            "reagent__tests",
            "reagent__tests__department",
        ),
        pk=stock_id,
    )

    # حماية نطاق القسم.
    # المدير ومدير المستشفى والمستخدم المركزي LAB
    # يستطيعون التعامل مع كامل المخزون.
    if not is_lab_manager(request.user):
        if not get_lab_user_stocks(
            request.user,
            LaboratoryReagentStock.objects.filter(
                pk=stock.pk
            )
        ).exists():
            return lab_access_denied(
                request,
                "لا يمكنك تنفيذ حركة على مخزون تابع لقسم مختبر آخر."
            )

    if request.method == "POST":
        movement_type = request.POST.get(
            "movement_type"
        )

        quantity = request.POST.get(
            "quantity"
        )

        try:
            quantity_decimal = Decimal(
                quantity
            )
        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ):
            quantity_decimal = Decimal("0")

        if quantity_decimal <= 0:
            messages.error(
                request,
                "يجب أن تكون الكمية أكبر من صفر."
            )

            return redirect(
                "laboratory:stock_movement",
                stock_id=stock.id,
            )

        if movement_type == "OUT":
            if quantity_decimal > stock.quantity:
                messages.error(
                    request,
                    "الكمية المطلوبة أكبر من الكمية الموجودة."
                )

                return redirect(
                    "laboratory:stock_movement",
                    stock_id=stock.id,
                )

            stock.quantity -= quantity_decimal

        elif movement_type == "IN":
            stock.quantity += quantity_decimal

        elif movement_type == "RETURN":
            stock.quantity += quantity_decimal

        elif movement_type == "ADJUSTMENT":
            stock.quantity = quantity_decimal

        else:
            messages.error(
                request,
                "نوع الحركة غير صحيح."
            )

            return redirect(
                "laboratory:stock_movement",
                stock_id=stock.id,
            )

        stock.save(
            update_fields=[
                "quantity",
                "updated_at",
            ]
        )

        LaboratoryStockMovement.objects.create(
            stock=stock,
            movement_type=movement_type,
            quantity=quantity_decimal,
            reference=request.POST.get(
                "reference",
                ""
            ).strip(),
            notes=request.POST.get(
                "notes",
                ""
            ).strip(),
            performed_by=request.user,
        )

        messages.success(
            request,
            "تم تسجيل حركة المخزون بنجاح."
        )

        return redirect(
            "laboratory:inventory_dashboard"
        )

    movements = stock.movements.select_related(
        "performed_by"
    ).order_by(
        "-created_at"
    )

    return render(
        request,
        "laboratory/stock_movement.html",
        {
            "stock": stock,
            "movements": movements,
        },
    )
