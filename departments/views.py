from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Department
from patients.models import Patient, Visit
from accounts.permissions import (
    get_user_department,
    user_has_access,
)
from laboratory.models import (
    LaboratoryOrder,
    LaboratoryOrderItem,
    LaboratoryResultDelivery,
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


def can_access_department(user, department):
    """
    التحكم في الوصول إلى لوحة القسم.

    ADMIN / MANAGER:
        يمكنهم الوصول إلى جميع الأقسام.

    بقية المستخدمين:
        يمكنهم الوصول إلى القسم المرتبط بحسابهم فقط.

    كما يجب أن يكون لدى المستخدم وصول إلى تطبيق departments.
    """

    if not user or not user.is_authenticated:
        return False

    if not user_has_access(user, "departments"):
        return False

    if is_manager(user):
        return True

    user_department = get_user_department(user)

    if not user_department or not department:
        return False

    return user_department.id == department.id


def get_department_or_forbidden(request, department_id):
    """
    جلب القسم مع التحقق من صلاحية المستخدم للوصول إليه.
    """

    department = get_object_or_404(
        Department,
        id=department_id,
        is_active=True,
    )

    if not can_access_department(request.user, department):
        messages.error(
            request,
            "ليس لديك صلاحية الوصول إلى هذا القسم.",
        )
        return None

    return department


@login_required
def department_list(request):
    """
    مركز أقسام المستشفى الرئيسي.

    ADMIN / MANAGER:
        عرض جميع الأقسام النشطة.

    المستخدم العادي:
        عرض القسم المرتبط بحسابه فقط.

    الصفحة تعرض مؤشرات HIS/LIS العامة
    مع إحصائيات تشغيلية لكل قسم.
    """

    user = request.user

    # =========================
    # الأقسام المسموح للمستخدم رؤيتها
    # =========================
    departments_qs = Department.objects.filter(
        is_active=True
    )

    if not is_manager(user):
        user_department = get_user_department(user)

        if user_department:
            departments_qs = departments_qs.filter(
                id=user_department.id
            )
        else:
            departments_qs = departments_qs.none()

    # =========================
    # البحث
    # =========================
    query = request.GET.get("q", "").strip()

    if query:
        departments_qs = departments_qs.filter(
            Q(name_ar__icontains=query)
            | Q(name_en__icontains=query)
            | Q(code__icontains=query)
        )

    # =========================
    # إحصائيات كل قسم
    # =========================
    departments = (
        departments_qs
        .annotate(
            patient_count=Count(
                "visits__patient",
                distinct=True,
            ),
            visit_count=Count(
                "visits",
                distinct=True,
            ),
            laboratory_order_count=Count(
                "laboratory_orders",
                distinct=True,
            ),
        )
        .order_by("name_ar")
    )

    # =========================
    # التاريخ الحالي
    # =========================
    today = timezone.localdate()

    # =========================
    # الإحصائيات العامة
    # =========================
    department_count = departments.count()

    if is_manager(user):
        active_count = Department.objects.filter(
            is_active=True
        ).count()
    else:
        active_count = department_count

    total_patients = Patient.objects.filter(
        visits__department__in=departments_qs
    ).distinct().count()

    today_visits = Visit.objects.filter(
        department__in=departments_qs,
        created_at__date=today,
    ).count()

    today_orders = LaboratoryOrder.objects.filter(
        requesting_department__in=departments_qs,
        requested_at__date=today,
    ).count()

    pending_orders = LaboratoryOrder.objects.filter(
        requesting_department__in=departments_qs,
        status__in=[
            "REQUESTED",
            "RECEIVED",
            "COLLECTED",
            "PROCESSING",
        ],
    ).count()

    pending_results = LaboratoryOrderItem.objects.filter(
        order__requesting_department__in=departments_qs,
        status__in=[
            "REQUESTED",
            "RECEIVED",
            "COLLECTED",
            "PROCESSING",
        ],
    ).count()

    completed_results = LaboratoryOrderItem.objects.filter(
        order__requesting_department__in=departments_qs,
        status="COMPLETED",
    ).count()

    critical_results = LaboratoryOrderItem.objects.filter(
        order__requesting_department__in=departments_qs,
        critical_status__in=[
            "CRITICAL_LOW",
            "CRITICAL_HIGH",
        ],
        verified=False,
    ).count()

    required_results = LaboratoryResultDelivery.objects.filter(
        department__in=departments_qs,
        received=False,
    ).count()

    # =========================
    # الإحصائيات الخاصة بكل قسم
    # =========================
    for department in departments:

        department.pending_orders_count = LaboratoryOrder.objects.filter(
            requesting_department=department,
            status__in=[
                "REQUESTED",
                "RECEIVED",
                "COLLECTED",
                "PROCESSING",
            ],
        ).count()

        department.pending_results_count = LaboratoryOrderItem.objects.filter(
            order__requesting_department=department,
            status__in=[
                "REQUESTED",
                "RECEIVED",
                "COLLECTED",
                "PROCESSING",
            ],
        ).count()

        department.critical_results_count = LaboratoryOrderItem.objects.filter(
            order__requesting_department=department,
            critical_status__in=[
                "CRITICAL_LOW",
                "CRITICAL_HIGH",
            ],
            verified=False,
        ).count()

        department.required_results_count = LaboratoryResultDelivery.objects.filter(
            department=department,
            received=False,
        ).count()

    return render(
        request,
        "departments/department_list.html",
        {
            "departments": departments,
            "query": query,

            "can_manage": is_manager(user),

            "department_count": department_count,
            "active_count": active_count,
            "total_patients": total_patients,
            "today_visits": today_visits,
            "today_orders": today_orders,

            "pending_orders": pending_orders,
            "pending_results": pending_results,
            "completed_results": completed_results,
            "critical_results": critical_results,
            "required_results": required_results,

            "today": today,
        },
    )


@login_required
def department_dashboard(request, department_id):
    department = get_department_or_forbidden(
        request,
        department_id,
    )

    if department is None:
        return redirect("departments:list")

    today = timezone.localdate()

    visits = (
        Visit.objects
        .filter(department=department)
        .select_related("patient", "doctor")
        .order_by("-created_at")
    )

    today_visits = visits.filter(
        created_at__date=today
    )

    patients = Patient.objects.filter(
        visits__department=department
    ).distinct().order_by("-created_at")

    # إحصاءات القسم الطبية الأساسية
    lab_results_panel = LaboratoryOrderItem.objects.filter(
        order__requesting_department=department
    ).select_related(
        "order", "order__patient", "test", "examiner"
    ).order_by("-updated_at")[:15]

    critical_results_panel = LaboratoryOrderItem.objects.filter(
        order__requesting_department=department,
        critical_status__isnull=False
    ).exclude(
        critical_status=""
    ).select_related(
        "order", "order__patient", "test", "examiner"
    ).order_by("-updated_at")[:10]

    unverified_results_panel = LaboratoryOrderItem.objects.filter(
        order__requesting_department=department,
        verified=False
    ).select_related(
        "order", "order__patient", "test", "examiner"
    ).order_by("-updated_at")[:10]

    lab_orders_panel = LaboratoryOrder.objects.filter(
        requesting_department=department
    ).select_related(
        "patient", "requesting_doctor"
    ).prefetch_related(
        "items"
    ).order_by("-requested_at")[:10]

    open_visits = visits.filter(status="OPEN").select_related(
        "patient", "doctor", "doctor__user"
    ).order_by("-created_at")[:10]

    opd_visit_count = visits.filter(visit_type="OPD").count()
    followup_visit_count = visits.filter(visit_type="FOLLOWUP").count()
    er_visit_count = visits.filter(visit_type="ER").count()

    male_patient_count = patients.filter(gender="M").count()
    female_patient_count = patients.filter(gender="F").count()

    orders = (
        LaboratoryOrder.objects
        .filter(requesting_department=department)
        .select_related(
            "patient",
            "visit",
            "requesting_doctor",
        )
        .prefetch_related("items__test")
        .order_by("-requested_at")
    )

    today_orders = orders.filter(
        requested_at__date=today
    )

    pending_orders = orders.filter(
        status__in=[
            "REQUESTED",
            "RECEIVED",
            "COLLECTED",
            "PROCESSING",
        ]
    )

    completed_orders = orders.filter(
        status="COMPLETED"
    )

    result_items = (
        LaboratoryOrderItem.objects
        .filter(order__requesting_department=department)
        .select_related(
            "order",
            "order__patient",
            "test",
        )
        .order_by("-updated_at")
    )

    pending_results = result_items.filter(
        status__in=[
            "REQUESTED",
            "RECEIVED",
            "COLLECTED",
            "PROCESSING",
        ]
    )

    unverified_results = result_items.filter(
        status="COMPLETED",
        verified=False,
    )

    critical_results = result_items.filter(
        critical_status__in=[
            "CRITICAL_LOW",
            "CRITICAL_HIGH",
        ],
        verified=False,
    )

    deliveries = (
        LaboratoryResultDelivery.objects
        .filter(department=department)
        .select_related(
            "order",
            "order__patient",
            "doctor",
        )
        .order_by("-sent_at")
    )

    pending_deliveries = deliveries.filter(
        received=False
    )

    completed_deliveries = deliveries.filter(
        received=True
    )

    today_completed = result_items.filter(
        status="COMPLETED",
        updated_at__date=today,
    ).count()

    today_deliveries = deliveries.filter(
        sent_at__date=today
    ).count()

    context = {
        "department": department,

        # المرضى
        "patients": patients[:12],
        "patient_count": patients.count(),

        # الزيارات
        "visits": visits[:12],
        "today_visits": today_visits[:12],
        "visit_count": visits.count(),
        "today_visit_count": today_visits.count(),

        # إحصاءات القسم
        "lab_results_panel": lab_results_panel,
        "critical_results_panel": critical_results_panel,
        "unverified_results_panel": unverified_results_panel,
        "lab_orders_panel": lab_orders_panel,
        "open_visits": open_visits,
        "opd_visit_count": opd_visit_count,
        "followup_visit_count": followup_visit_count,
        "er_visit_count": er_visit_count,
        "male_patient_count": male_patient_count,
        "female_patient_count": female_patient_count,

        # المختبر
        "orders": orders[:12],
        "today_orders": today_orders[:12],
        "pending_orders": pending_orders[:12],
        "completed_orders": completed_orders[:12],

        "order_count": orders.count(),
        "today_order_count": today_orders.count(),
        "pending_order_count": pending_orders.count(),
        "completed_order_count": completed_orders.count(),

        # النتائج
        "pending_results": pending_results[:12],
        "unverified_results": unverified_results[:12],
        "critical_results": critical_results[:12],

        "pending_result_count": pending_results.count(),
        "unverified_result_count": unverified_results.count(),
        "critical_result_count": critical_results.count(),

        # التسليم
        "deliveries": deliveries[:12],
        "pending_deliveries": pending_deliveries[:12],
        "completed_deliveries": completed_deliveries[:12],

        "delivery_count": deliveries.count(),
        "pending_delivery_count": pending_deliveries.count(),
        "completed_delivery_count": completed_deliveries.count(),

        # الإنجازات
        "today_completed": today_completed,
        "today_deliveries": today_deliveries,

        "can_manage": is_manager(request.user),
        "today": today,
    }

    return render(
        request,
        "departments/department_dashboard.html",
        context,
    )


@login_required
def department_create(request):
    if not is_manager(request.user):
        messages.error(request, "ليس لديك صلاحية إضافة الأقسام.")
        return redirect("departments:list")

    if request.method == "POST":
        name_ar = request.POST.get("name_ar", "").strip()
        name_en = request.POST.get("name_en", "").strip()
        code = request.POST.get("code", "").strip().upper()
        department_type = request.POST.get(
            "department_type",
            "CLINICAL",
        )
        phone = request.POST.get("phone", "").strip()
        location = request.POST.get("location", "").strip()

        if not name_ar or not name_en or not code:
            messages.error(
                request,
                "يرجى إدخال اسم القسم والكود.",
            )

        elif Department.objects.filter(code=code).exists():
            messages.error(
                request,
                "كود القسم مستخدم بالفعل.",
            )

        else:
            Department.objects.create(
                name_ar=name_ar,
                name_en=name_en,
                code=code,
                department_type=department_type,
                phone=phone,
                location=location,
            )

            messages.success(
                request,
                "تمت إضافة القسم بنجاح.",
            )

            return redirect("departments:list")

    return render(
        request,
        "departments/department_form.html",
        {
            "department": None,
            "department_types": Department.DEPARTMENT_TYPES,
        },
    )


@login_required
def department_edit(request, department_id):
    if not is_manager(request.user):
        messages.error(
            request,
            "ليس لديك صلاحية تعديل الأقسام.",
        )
        return redirect("departments:list")

    department = get_object_or_404(
        Department,
        id=department_id,
    )

    if request.method == "POST":
        name_ar = request.POST.get("name_ar", "").strip()
        name_en = request.POST.get("name_en", "").strip()
        code = request.POST.get("code", "").strip().upper()
        department_type = request.POST.get(
            "department_type",
            "CLINICAL",
        )
        phone = request.POST.get("phone", "").strip()
        location = request.POST.get("location", "").strip()

        duplicate = (
            Department.objects
            .filter(code=code)
            .exclude(id=department.id)
            .exists()
        )

        if not name_ar or not name_en or not code:
            messages.error(
                request,
                "يرجى إدخال اسم القسم والكود.",
            )

        elif duplicate:
            messages.error(
                request,
                "كود القسم مستخدم بالفعل.",
            )

        else:
            department.name_ar = name_ar
            department.name_en = name_en
            department.code = code
            department.department_type = department_type
            department.phone = phone
            department.location = location
            department.save()

            messages.success(
                request,
                "تم تعديل القسم بنجاح.",
            )

            return redirect("departments:list")

    return render(
        request,
        "departments/department_form.html",
        {
            "department": department,
            "department_types": Department.DEPARTMENT_TYPES,
        },
    )


@login_required
def department_toggle(request, department_id):
    if not is_manager(request.user):
        messages.error(
            request,
            "ليس لديك صلاحية تغيير حالة القسم.",
        )
        return redirect("departments:list")

    department = get_object_or_404(
        Department,
        id=department_id,
    )

    if request.method == "POST":
        department.is_active = not department.is_active

        department.save(
            update_fields=[
                "is_active",
                "updated_at",
            ]
        )

        messages.success(
            request,
            "تم تحديث حالة القسم بنجاح.",
        )

    return redirect("departments:list")


# ============================================================
# DEPARTMENT OPERATIONS
# ============================================================

@login_required
def department_patients(request, department_id):
    department = get_department_or_forbidden(
        request,
        department_id,
    )

    if department is None:
        return redirect("departments:list")

    patients = (
        Patient.objects
        .filter(visits__department=department)
        .distinct()
        .order_by("-created_at")
    )

    query = request.GET.get("q", "").strip()

    if query:
        patients = patients.filter(
            Q(full_name__icontains=query)
            | Q(patient_number__icontains=query)
            | Q(phone__icontains=query)
        )

    return render(
        request,
        "departments/department_patients.html",
        {
            "department": department,
            "patients": patients,
            "query": query,
            "patient_count": patients.count(),
        },
    )


@login_required
def department_visits(request, department_id):
    department = get_department_or_forbidden(
        request,
        department_id,
    )

    if department is None:
        return redirect("departments:list")

    visits = (
        Visit.objects
        .filter(department=department)
        .select_related(
            "patient",
            "doctor",
        )
        .order_by("-created_at")
    )

    query = request.GET.get("q", "").strip()

    if query:
        visits = visits.filter(
            Q(patient__full_name__icontains=query)
            | Q(patient__patient_number__icontains=query)
            | Q(visit_number__icontains=query)
        )

    status = request.GET.get("status", "").strip()

    if status:
        visits = visits.filter(status=status)

    return render(
        request,
        "departments/department_visits.html",
        {
            "department": department,
            "visits": visits,
            "query": query,
            "selected_status": status,
            "status_choices": Visit.STATUS_CHOICES,
            "visit_count": visits.count(),
        },
    )


@login_required
def department_lab_orders(request, department_id):
    department = get_department_or_forbidden(
        request,
        department_id,
    )

    if department is None:
        return redirect("departments:list")

    orders = (
        LaboratoryOrder.objects
        .filter(requesting_department=department)
        .select_related(
            "patient",
            "visit",
            "requesting_doctor",
        )
        .prefetch_related(
            "items__test",
        )
        .order_by("-requested_at")
    )

    query = request.GET.get("q", "").strip()

    if query:
        orders = orders.filter(
            Q(order_number__icontains=query)
            | Q(patient__full_name__icontains=query)
            | Q(patient__patient_number__icontains=query)
        )

    status = request.GET.get("status", "").strip()

    if status:
        orders = orders.filter(status=status)

    priority = request.GET.get("priority", "").strip()

    if priority:
        orders = orders.filter(priority=priority)

    return render(
        request,
        "departments/department_lab_orders.html",
        {
            "department": department,
            "orders": orders,
            "query": query,
            "selected_status": status,
            "selected_priority": priority,
            "status_choices": LaboratoryOrder.STATUS_CHOICES,
            "priority_choices": LaboratoryOrder.PRIORITY_CHOICES,
            "order_count": orders.count(),
        },
    )


@login_required
def department_results(request, department_id):
    department = get_department_or_forbidden(
        request,
        department_id,
    )

    if department is None:
        return redirect("departments:list")

    results = (
        LaboratoryOrderItem.objects
        .filter(
            order__requesting_department=department,
        )
        .select_related(
            "order",
            "order__patient",
            "test",
            "examiner",
            "verified_by",
        )
        .order_by("-updated_at")
    )

    query = request.GET.get("q", "").strip()

    if query:
        results = results.filter(
            Q(order__order_number__icontains=query)
            | Q(order__patient__full_name__icontains=query)
            | Q(
                order__patient__patient_number__icontains=query
            )
            | Q(test__name_en__icontains=query)
            | Q(test__name_ar__icontains=query)
        )

    result_filter = request.GET.get(
        "filter",
        "",
    ).strip()

    if result_filter == "pending":
        results = results.filter(
            status__in=[
                "REQUESTED",
                "RECEIVED",
                "COLLECTED",
                "PROCESSING",
            ]
        )

    elif result_filter == "completed":
        results = results.filter(
            status="COMPLETED",
        )

    elif result_filter == "unverified":
        results = results.filter(
            status="COMPLETED",
            verified=False,
        )

    elif result_filter == "critical":
        results = results.filter(
            critical_status__in=[
                "CRITICAL_LOW",
                "CRITICAL_HIGH",
            ],
            verified=False,
        )

    return render(
        request,
        "departments/department_results.html",
        {
            "department": department,
            "results": results,
            "query": query,
            "result_filter": result_filter,
            "result_count": results.count(),
        },
    )


@login_required
def department_required_results(request, department_id):
    department = get_department_or_forbidden(
        request,
        department_id,
    )

    if department is None:
        return redirect("departments:list")

    deliveries = (
        LaboratoryResultDelivery.objects
        .filter(
            department=department,
            received=False,
        )
        .select_related(
            "order",
            "order__patient",
            "doctor",
        )
        .prefetch_related(
            "order__items__test",
        )
        .order_by("-sent_at")
    )

    return render(
        request,
        "departments/department_required_results.html",
        {
            "department": department,
            "deliveries": deliveries,
            "delivery_count": deliveries.count(),
        },
    )


@login_required
def department_achievements(request, department_id):
    department = get_department_or_forbidden(
        request,
        department_id,
    )

    if department is None:
        return redirect("departments:list")

    today = timezone.localdate()

    today_visits = Visit.objects.filter(
        department=department,
        created_at__date=today,
    ).count()

    today_orders = LaboratoryOrder.objects.filter(
        requesting_department=department,
        requested_at__date=today,
    ).count()

    today_completed_results = LaboratoryOrderItem.objects.filter(
        order__requesting_department=department,
        status="COMPLETED",
        updated_at__date=today,
    ).count()

    today_verified_results = LaboratoryOrderItem.objects.filter(
        order__requesting_department=department,
        status="COMPLETED",
        verified=True,
        verified_at__date=today,
    ).count()

    today_deliveries = LaboratoryResultDelivery.objects.filter(
        department=department,
        sent_at__date=today,
    ).count()

    return render(
        request,
        "departments/department_achievements.html",
        {
            "department": department,
            "today": today,
            "today_visits": today_visits,
            "today_orders": today_orders,
            "today_completed_results": today_completed_results,
            "today_verified_results": today_verified_results,
            "today_deliveries": today_deliveries,
        },
    )
