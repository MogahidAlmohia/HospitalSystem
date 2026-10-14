from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from departments.models import Department
from .models import StaffProfile
from .permissions import (
    ROLE_PERMISSIONS,
    PERMISSION_GROUPS,
    get_user_department,
    get_user_role,
)


def is_admin(user):
    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    try:
        return user.staff_profile.role in ["ADMIN", "MANAGER"]
    except StaffProfile.DoesNotExist:
        return False


def logout_view(request):
    logout(request)
    return redirect("/accounts/login/")


@login_required
def dashboard(request):
    """لوحة التحكم الرئيسية لنظام إدارة المستشفى والمختبر."""
    try:
        if not request.user.staff_profile.is_active:
            logout(request)
            return redirect("accounts:login")
    except StaffProfile.DoesNotExist:
        logout(request)
        return redirect("accounts:login")

    role = get_user_role(request.user)
    user_department = get_user_department(request.user)

    if role in {"ADMIN", "MANAGER"}:
        pass
    elif role == "LAB":
        return redirect("laboratory:dashboard")
    elif role == "RECEPTION":
        return redirect("reception:dashboard")
    elif role == "EMERGENCY":
        return redirect("emergency:dashboard")
    elif role == "INPATIENT":
        return redirect("inpatient:dashboard")
    elif role in {
        "DOCTOR",
        "RADIOLOGY",
        "PHARMACY",
        "NURSING",
        "SURGERY",
        "BLOOD_BANK",
        "BILLING",
        "INVENTORY",
        "OTHER",
    }:
        if user_department and user_department.is_active:
            return redirect(
                "departments:dashboard",
                department_id=user_department.id,
            )

    from django.urls import reverse
    from django.utils import timezone

    from patients.models import Patient, Visit
    from doctors.models import Doctor
    from laboratory.models import (
        LaboratoryOrder,
        LaboratoryOrderItem,
        LaboratoryResultDelivery,
    )
    from inpatient.models import Admission, Bed
    from emergency.models import EmergencyCase

    now = timezone.localtime()
    today = now.date()

    total_patients = Patient.objects.count()
    active_patients = Patient.objects.filter(is_active=True).count()
    today_patients = Patient.objects.filter(created_at__date=today).count()
    today_visits = Visit.objects.filter(created_at__date=today).count()
    open_visits = Visit.objects.filter(status__in=["OPEN", "IN_PROGRESS"]).count()
    recent_patients = Patient.objects.order_by("-created_at")[:8]
    recent_visits = (
        Visit.objects.select_related("patient", "department", "doctor")
        .order_by("-created_at")[:8]
    )

    total_doctors = Doctor.objects.filter(is_active=True).count()
    total_departments = Department.objects.filter(is_active=True).count()

    active_admissions = Admission.objects.filter(status="ADMITTED").count()
    transferred_admissions = Admission.objects.filter(status="TRANSFERRED").count()
    occupied_beds = Bed.objects.filter(status="OCCUPIED").count()
    available_beds = Bed.objects.filter(status="AVAILABLE").count()
    reserved_beds = Bed.objects.filter(status="RESERVED").count()
    maintenance_beds = Bed.objects.filter(status="MAINTENANCE").count()
    operational_beds = Bed.objects.exclude(status="INACTIVE").count()
    bed_occupancy_percent = (
        round((occupied_beds / operational_beds) * 100) if operational_beds else 0
    )

    recent_admissions = (
        Admission.objects.select_related(
            "patient",
            "department",
            "doctor",
            "room",
            "bed",
        )
        .order_by("-admitted_at")[:8]
    )

    emergency_active_statuses = ["WAITING", "TRIAGE", "UNDER_CARE", "OBSERVATION"]
    emergency_active = EmergencyCase.objects.filter(
        status__in=emergency_active_statuses
    ).count()
    emergency_waiting = EmergencyCase.objects.filter(status="WAITING").count()
    emergency_triage = EmergencyCase.objects.filter(status="TRIAGE").count()
    emergency_under_care = EmergencyCase.objects.filter(status="UNDER_CARE").count()
    emergency_critical = EmergencyCase.objects.filter(
        status__in=emergency_active_statuses,
        triage_level__in=["RED", "ORANGE"],
    ).count()
    recent_emergency = (
        EmergencyCase.objects.select_related("patient", "department", "doctor")
        .order_by("-id")[:8]
    )

    today_lab_orders = LaboratoryOrder.objects.filter(requested_at__date=today).count()
    pending_lab_orders = LaboratoryOrder.objects.filter(
        status__in=["REQUESTED", "RECEIVED", "COLLECTED", "PROCESSING"]
    ).count()
    processing_lab_orders = LaboratoryOrder.objects.filter(status="PROCESSING").count()
    completed_lab_orders = LaboratoryOrder.objects.filter(status="COMPLETED").count()
    urgent_pending_lab_orders = LaboratoryOrder.objects.filter(
        priority__in=["URGENT", "STAT"],
        status__in=["REQUESTED", "RECEIVED", "COLLECTED", "PROCESSING"],
    ).count()

    pending_result_items = (
        LaboratoryOrderItem.objects.filter(verified=False)
        .filter((Q(result__isnull=False) & ~Q(result="")) | Q(result_numeric__isnull=False))
        .exclude(status="CANCELLED")
        .exclude(status="REJECTED")
        .select_related("order", "order__patient", "test", "examiner")
        .order_by("-updated_at")[:10]
    )

    pending_verification_count = (
        LaboratoryOrderItem.objects.filter(verified=False)
        .filter((Q(result__isnull=False) & ~Q(result="")) | Q(result_numeric__isnull=False))
        .exclude(status="CANCELLED")
        .exclude(status="REJECTED")
        .count()
    )

    pending_result_orders_count = (
        LaboratoryOrderItem.objects.filter(verified=False)
        .filter((Q(result__isnull=False) & ~Q(result="")) | Q(result_numeric__isnull=False))
        .exclude(status="CANCELLED")
        .exclude(status="REJECTED")
        .values("order_id")
        .distinct()
        .count()
    )

    integrity_problem_items = (
        LaboratoryOrderItem.objects.filter(status="COMPLETED")
        .filter(
            Q(verified=False)
            | ((Q(result__isnull=True) | Q(result="")) & Q(result_numeric__isnull=True))
        )
        .select_related("order", "order__patient", "test")
        .order_by("-updated_at", "-id")
    )
    integrity_problem_count = integrity_problem_items.count()

    pending_result_deliveries = LaboratoryResultDelivery.objects.filter(received=False).count()
    today_result_deliveries = LaboratoryResultDelivery.objects.filter(sent_at__date=today).count()

    recent_lab_orders = (
        LaboratoryOrder.objects.select_related(
            "patient",
            "requesting_department",
            "requesting_doctor",
        )
        .order_by("-requested_at")[:10]
    )

    alerts = []
    if emergency_critical:
        alerts.append({
            "level": "danger",
            "icon": "🚨",
            "title": "حالات طوارئ حرجة",
            "count": emergency_critical,
            "text": "حالات RED / ORANGE تحتاج متابعة عاجلة.",
            "url": reverse("emergency:dashboard"),
        })

    if urgent_pending_lab_orders:
        alerts.append({
            "level": "warning",
            "icon": "⚡",
            "title": "طلبات مختبر عاجلة",
            "count": urgent_pending_lab_orders,
            "text": "طلبات URGENT / STAT ما زالت قيد التنفيذ.",
            "url": reverse("laboratory:result_workflow_dashboard"),
        })

    if pending_verification_count:
        alerts.append({
            "level": "warning",
            "icon": "🧪",
            "title": "نتائج بانتظار الاعتماد",
            "count": pending_verification_count,
            "text": "نتائج تم إدخالها ولم يتم اعتمادها بعد.",
            "url": reverse("laboratory:result_workflow_dashboard"),
        })

    if pending_result_deliveries:
        alerts.append({
            "level": "info",
            "icon": "📤",
            "title": "نتائج بانتظار تأكيد الاستلام",
            "count": pending_result_deliveries,
            "text": "نتائج تم إرسالها ولم يؤكد القسم أو الطبيب استلامها.",
            "url": reverse("laboratory:result_delivery_dashboard"),
        })

    if integrity_problem_count:
        alerts.append({
            "level": "danger",
            "icon": "⚠️",
            "title": "تنبيه سلامة بيانات المختبر",
            "count": integrity_problem_count,
            "text": "توجد نتائج بحالة مكتملة لكنها غير معتمدة أو بدون نتيجة.",
            "url": reverse("laboratory:result_workflow_dashboard"),
        })

    if available_beds == 0:
        alerts.append({
            "level": "danger",
            "icon": "🛏️",
            "title": "لا توجد أسرة متاحة",
            "count": 0,
            "text": "جميع الأسرة التشغيلية غير متاحة حاليًا.",
            "url": reverse("inpatient:bed_list"),
        })

    department_summary = []
    active_departments = Department.objects.filter(is_active=True).order_by("name_ar")

    for department in active_departments:
        department_visits = Visit.objects.filter(
            department_id=department.id
        ).filter(status__in=["OPEN", "IN_PROGRESS"]).count()
        department_admissions = Admission.objects.filter(
            department_id=department.id,
            status="ADMITTED",
        ).count()
        department_lab_orders = LaboratoryOrder.objects.filter(
            requesting_department_id=department.id,
            status__in=["REQUESTED", "RECEIVED", "COLLECTED", "PROCESSING"],
        ).count()

        activity_total = department_visits + department_admissions + department_lab_orders
        if activity_total > 0:
            department_status = "ACTIVE"
            department_status_ar = "نشط"
        else:
            department_status = "IDLE"
            department_status_ar = "لا توجد حركة"

        department_summary.append({
            "id": department.id,
            "name_ar": department.name_ar,
            "name_en": department.name_en,
            "visits": department_visits,
            "admissions": department_admissions,
            "lab_orders": department_lab_orders,
            "activity": activity_total,
            "status": department_status,
            "status_ar": department_status_ar,
        })

    chart_data = {
        "emergency": {
            "waiting": emergency_waiting,
            "triage": emergency_triage,
            "under_care": emergency_under_care,
            "critical": emergency_critical,
        },
        "laboratory": {
            "today": today_lab_orders,
            "pending": pending_lab_orders,
            "processing": processing_lab_orders,
            "completed": completed_lab_orders,
            "verification": pending_verification_count,
            "deliveries": pending_result_deliveries,
        },
        "beds": {
            "occupied": occupied_beds,
            "available": available_beds,
            "reserved": reserved_beds,
            "maintenance": maintenance_beds,
        },
    }

    quick_actions = [
        {"title": "تسجيل مريض", "icon": "👤", "url": reverse("reception:register_patient"), "class": "primary"},
        {"title": "بحث عن مريض", "icon": "🔍", "url": reverse("patients:search"), "class": "info"},
        {"title": "تنويم مريض", "icon": "🛏️", "url": reverse("inpatient:admission_create"), "class": "success"},
        {"title": "حالة طوارئ", "icon": "🚑", "url": reverse("emergency:create"), "class": "danger"},
        {"title": "استقبال عينات", "icon": "🧪", "url": reverse("laboratory:sample_reception"), "class": "purple"},
        {"title": "متابعة النتائج", "icon": "📋", "url": reverse("laboratory:result_workflow_dashboard"), "class": "warning"},
        {"title": "إرسال النتائج", "icon": "📤", "url": reverse("laboratory:result_delivery_dashboard"), "class": "secondary"},
        {"title": "الأطباء", "icon": "👨‍⚕️", "url": reverse("doctors:list"), "class": "dark"},
    ]

    context = {
        "now": now,
        "today": today,
        "total_patients": total_patients,
        "active_patients": active_patients,
        "today_patients": today_patients,
        "today_visits": today_visits,
        "open_visits": open_visits,
        "recent_patients": recent_patients,
        "recent_visits": recent_visits,
        "total_doctors": total_doctors,
        "total_departments": total_departments,
        "active_admissions": active_admissions,
        "transferred_admissions": transferred_admissions,
        "occupied_beds": occupied_beds,
        "available_beds": available_beds,
        "reserved_beds": reserved_beds,
        "maintenance_beds": maintenance_beds,
        "operational_beds": operational_beds,
        "bed_occupancy_percent": bed_occupancy_percent,
        "recent_admissions": recent_admissions,
        "emergency_active": emergency_active,
        "emergency_waiting": emergency_waiting,
        "emergency_triage": emergency_triage,
        "emergency_under_care": emergency_under_care,
        "emergency_critical": emergency_critical,
        "recent_emergency": recent_emergency,
        "today_lab_orders": today_lab_orders,
        "pending_lab_orders": pending_lab_orders,
        "processing_lab_orders": processing_lab_orders,
        "completed_lab_orders": completed_lab_orders,
        "urgent_pending_lab_orders": urgent_pending_lab_orders,
        "pending_verification_count": pending_verification_count,
        "pending_result_orders_count": pending_result_orders_count,
        "pending_result_items": pending_result_items,
        "integrity_problem_count": integrity_problem_count,
        "integrity_problem_items": integrity_problem_items[:10],
        "pending_result_deliveries": pending_result_deliveries,
        "today_result_deliveries": today_result_deliveries,
        "recent_lab_orders": recent_lab_orders,
        "alerts": alerts,
        "quick_actions": quick_actions,
        "department_summary": department_summary,
        "chart_data": chart_data,
    }

    return render(request, "accounts/dashboard.html", context)


def login_view(request):
    """Hospital login page."""
    if request.user.is_authenticated:
        try:
            if request.user.staff_profile.is_active:
                return redirect("accounts:dashboard")
        except StaffProfile.DoesNotExist:
            pass

    login_users = (
        User.objects.filter(is_active=True, staff_profile__is_active=True)
        .select_related("staff_profile", "staff_profile__department")
        .order_by("staff_profile__full_name", "username")
    )

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_active:
            try:
                if not user.staff_profile.is_active:
                    messages.error(request, "حساب الموظف غير نشط.")
                    return render(request, "accounts/login.html", {"login_users": login_users})
            except StaffProfile.DoesNotExist:
                messages.error(request, "لا يوجد ملف موظف مرتبط بهذا الحساب.")
                return render(request, "accounts/login.html", {"login_users": login_users})

            login(request, user)
            return redirect("accounts:dashboard")

        messages.error(request, "اسم المستخدم أو كلمة المرور غير صحيحة.")

    return render(request, "accounts/login.html", {"login_users": login_users})


@login_required
@user_passes_test(is_admin)
def hr_dashboard(request):
    """لوحة الموارد البشرية."""
    profiles = StaffProfile.objects.select_related("user", "department").order_by("full_name")
    query = request.GET.get("q", "").strip()
    role = request.GET.get("role", "").strip()
    department_id = request.GET.get("department", "").strip()

    if query:
        profiles = profiles.filter(
            Q(full_name__icontains=query)
            | Q(employee_number__icontains=query)
            | Q(phone__icontains=query)
            | Q(user__username__icontains=query)
        )
    if role:
        profiles = profiles.filter(role=role)
    if department_id:
        profiles = profiles.filter(department_id=department_id)

    all_profiles = StaffProfile.objects.select_related("department")
    department_rows = []
    for department in Department.objects.filter(is_active=True).order_by("name_ar"):
        department_rows.append({
            "department": department,
            "count": all_profiles.filter(department=department).count(),
            "active": all_profiles.filter(department=department, is_active=True).count(),
        })

    context = {
        "profiles": profiles[:100],
        "departments": Department.objects.filter(is_active=True).order_by("name_ar"),
        "roles": StaffProfile.ROLE_CHOICES,
        "department_rows": department_rows,
        "query": query,
        "selected_role": role,
        "selected_department": department_id,
        "total_staff": all_profiles.count(),
        "active_staff": all_profiles.filter(is_active=True).count(),
        "inactive_staff": all_profiles.filter(is_active=False).count(),
        "unassigned_staff": all_profiles.filter(department__isnull=True).count(),
        "new_staff": all_profiles.order_by("-created_at")[:5],
    }
    return render(request, "accounts/hr_dashboard.html", context)


@login_required
@user_passes_test(is_admin)
def user_list(request):
    query = request.GET.get("q", "").strip()
    role = request.GET.get("role", "").strip()
    department_id = request.GET.get("department", "").strip()

    users = User.objects.select_related("staff_profile", "staff_profile__department").all()
    if query:
        users = users.filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(staff_profile__full_name__icontains=query)
            | Q(staff_profile__employee_number__icontains=query)
        )

    if role:
        users = users.filter(staff_profile__role=role)

    if department_id:
        users = users.filter(staff_profile__department_id=department_id)

    users = users.order_by("username")

    context = {
        "users": users,
        "departments": Department.objects.filter(is_active=True).order_by("name_ar"),
        "roles": StaffProfile.ROLE_CHOICES,
        "query": query,
        "selected_role": role,
        "selected_department": department_id,
        "total_users": User.objects.count(),
        "active_users": User.objects.filter(is_active=True).count(),
        "staff_count": StaffProfile.objects.count(),
    }
    return render(request, "accounts/user_list.html", context)


@login_required
@user_passes_test(is_admin)
def user_create(request):
    departments = Department.objects.filter(is_active=True).order_by("name_ar")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        password2 = request.POST.get("password2", "")
        employee_number = request.POST.get("employee_number", "").strip()
        full_name = request.POST.get("full_name", "").strip()
        role = request.POST.get("role", "OTHER")
        department_id = request.POST.get("department") or None
        phone = request.POST.get("phone", "").strip()

        valid_roles = {value for value, label in StaffProfile.ROLE_CHOICES}
        if role not in valid_roles:
            messages.error(request, "الدور الوظيفي المحدد غير صالح.")
            return render(request, "accounts/user_form.html", {"departments": departments, "roles": StaffProfile.ROLE_CHOICES})

        if department_id and not Department.objects.filter(pk=department_id, is_active=True).exists():
            messages.error(request, "القسم المحدد غير موجود أو غير نشط.")
            return render(request, "accounts/user_form.html", {"departments": departments, "roles": StaffProfile.ROLE_CHOICES})

        if not username or not password or not employee_number or not full_name:
            messages.error(request, "يرجى تعبئة جميع الحقول المطلوبة.")
            return render(request, "accounts/user_form.html", {"departments": departments, "roles": StaffProfile.ROLE_CHOICES})

        if password != password2:
            messages.error(request, "كلمتا المرور غير متطابقتين.")
            return render(request, "accounts/user_form.html", {"departments": departments, "roles": StaffProfile.ROLE_CHOICES})

        if User.objects.filter(username=username).exists():
            messages.error(request, "اسم المستخدم موجود مسبقًا.")
            return render(request, "accounts/user_form.html", {"departments": departments, "roles": StaffProfile.ROLE_CHOICES})

        if StaffProfile.objects.filter(employee_number=employee_number).exists():
            messages.error(request, "الرقم الوظيفي موجود مسبقًا.")
            return render(request, "accounts/user_form.html", {"departments": departments, "roles": StaffProfile.ROLE_CHOICES})

        user = User.objects.create_user(username=username, password=password)
        profile = StaffProfile.objects.create(
            user=user,
            employee_number=employee_number,
            full_name=full_name,
            role=role,
            department_id=department_id,
            phone=phone,
            is_active=True,
        )

        messages.success(request, f"تم إنشاء المستخدم {profile.full_name} بنجاح.")
        return redirect("accounts:user_list")

    return render(request, "accounts/user_form.html", {"departments": departments, "roles": StaffProfile.ROLE_CHOICES})


@login_required
@user_passes_test(is_admin)
def user_edit(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    profile, created = StaffProfile.objects.get_or_create(
        user=user,
        defaults={
            "employee_number": f"EMP-{user.id}",
            "full_name": user.get_full_name() or user.username,
            "role": "OTHER",
        },
    )

    departments = Department.objects.filter(is_active=True).order_by("name_ar")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        employee_number = request.POST.get("employee_number", "").strip()
        full_name = request.POST.get("full_name", "").strip()
        role = request.POST.get("role", "OTHER")
        department_id = request.POST.get("department") or None
        phone = request.POST.get("phone", "").strip()
        new_password = request.POST.get("password", "")
        new_password2 = request.POST.get("password2", "")

        if not username or not employee_number or not full_name:
            messages.error(request, "يرجى تعبئة الحقول المطلوبة.")
            return render(request, "accounts/user_form.html", {"edit_mode": True, "user_obj": user, "profile": profile, "departments": departments, "roles": StaffProfile.ROLE_CHOICES})

        if User.objects.exclude(pk=user.pk).filter(username=username).exists():
            messages.error(request, "اسم المستخدم مستخدم من حساب آخر.")
            return render(request, "accounts/user_form.html", {"edit_mode": True, "user_obj": user, "profile": profile, "departments": departments, "roles": StaffProfile.ROLE_CHOICES})

        if StaffProfile.objects.exclude(pk=profile.pk).filter(employee_number=employee_number).exists():
            messages.error(request, "الرقم الوظيفي مستخدم من موظف آخر.")
            return render(request, "accounts/user_form.html", {"edit_mode": True, "user_obj": user, "profile": profile, "departments": departments, "roles": StaffProfile.ROLE_CHOICES})

        if new_password:
            if new_password != new_password2:
                messages.error(request, "كلمتا المرور غير متطابقتين.")
                return render(request, "accounts/user_form.html", {"edit_mode": True, "user_obj": user, "profile": profile, "departments": departments, "roles": StaffProfile.ROLE_CHOICES})
            user.set_password(new_password)

        user.username = username
        user.save()

        profile.employee_number = employee_number
        profile.full_name = full_name
        profile.role = role
        profile.department_id = department_id
        profile.phone = phone
        profile.save()

        messages.success(request, "تم تحديث بيانات المستخدم بنجاح.")
        return redirect("accounts:user_list")

    return render(request, "accounts/user_form.html", {"edit_mode": True, "user_obj": user, "profile": profile, "departments": departments, "roles": StaffProfile.ROLE_CHOICES})


@login_required
@user_passes_test(is_admin)
def user_toggle(request, user_id):
    user = get_object_or_404(User, pk=user_id)

    if user == request.user:
        messages.error(request, "لا يمكنك تعطيل حسابك الحالي.")
        return redirect("accounts:user_list")

    user.is_active = not user.is_active
    user.save(update_fields=["is_active"])

    try:
        profile = user.staff_profile
        profile.is_active = user.is_active
        profile.save(update_fields=["is_active"])
    except StaffProfile.DoesNotExist:
        pass

    state = "تم تفعيل المستخدم." if user.is_active else "تم تعطيل المستخدم."
    messages.success(request, state)
    return redirect("accounts:user_list")


@login_required
@user_passes_test(is_admin)
def user_permissions(request, user_id):
    """إدارة الصلاحيات الفردية للمستخدم."""
    target_user = get_object_or_404(User, pk=user_id)

    profile, created = StaffProfile.objects.get_or_create(
        user=target_user,
        defaults={
            "employee_number": f"EMP-{target_user.id:05d}",
            "full_name": target_user.get_full_name() or target_user.username,
            "role": "OTHER",
        },
    )

    permission_groups = PERMISSION_GROUPS
    valid_permissions = {
        permission
        for group in permission_groups.values()
        for permission, label in group["permissions"]
    }

    if request.method == "POST":
        allowed = request.POST.getlist("allowed_permissions")
        denied = request.POST.getlist("denied_permissions")

        profile.custom_permissions = [
            permission for permission in allowed if permission in valid_permissions
        ]
        profile.denied_permissions = [
            permission for permission in denied if permission in valid_permissions
        ]
        profile.custom_permissions = [
            permission for permission in profile.custom_permissions if permission not in profile.denied_permissions
        ]

        profile.save(update_fields=["custom_permissions", "denied_permissions", "updated_at"])

        messages.success(request, f"تم حفظ صلاحيات المستخدم {target_user.username} بنجاح.")
        return redirect("accounts:user_permissions", user_id=target_user.id)

    custom_permissions = set(profile.custom_permissions or [])
    denied_permissions = set(profile.denied_permissions or [])
    role = profile.role
    role_permissions = set(ROLE_PERMISSIONS.get(role, set()))
    is_full_access = "*" in role_permissions
    effective_permissions = (role_permissions | custom_permissions) - denied_permissions

    context = {
        "target_user": target_user,
        "profile": profile,
        "permission_groups": permission_groups,
        "custom_permissions": custom_permissions,
        "denied_permissions": denied_permissions,
        "role_permissions": role_permissions,
        "effective_permissions": effective_permissions,
        "is_full_access": is_full_access,
    }
    return render(request, "accounts/user_permissions.html", context)
