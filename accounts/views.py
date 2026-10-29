from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

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
        return user.staff_profile.role in {"ADMIN", "MANAGER"}
    except StaffProfile.DoesNotExist:
        return False


def logout_view(request):
    logout(request)
    return redirect("/accounts/login/")


@login_required
def dashboard(request):
    """لوحة التحكم الرئيسية للنظام."""
    role = get_user_role(request.user)
    user_department = get_user_department(request.user)

    if role == "LAB":
        return redirect("laboratory:dashboard")
    if role == "RECEPTION":
        return redirect("reception:dashboard")
    if role == "EMERGENCY":
        return redirect("emergency:dashboard")
    if role == "INPATIENT":
        return redirect("inpatient:dashboard")
    if role in {"ADMIN", "MANAGER"}:
        pass
    elif user_department and user_department.is_active:
        return redirect("departments:dashboard", department_id=user_department.id)

    from patients.models import Patient, Visit
    from doctors.models import Doctor
    from inpatient.models import Admission, Bed
    from emergency.models import EmergencyCase

    from laboratory.models import LaboratoryOrder, LaboratoryOrderItem, LaboratoryResultDelivery

    today = timezone.localtime().date()

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
    occupied_beds = Bed.objects.filter(status="OCCUPIED").count()
    available_beds = Bed.objects.filter(status="AVAILABLE").count()
    reserved_beds = Bed.objects.filter(status="RESERVED").count()
    maintenance_beds = Bed.objects.filter(status="MAINTENANCE").count()
    operational_beds = Bed.objects.exclude(status="INACTIVE").count()
    bed_occupancy_percent = (
        round((occupied_beds / operational_beds) * 100) if operational_beds else 0
    )

    emergency_active = EmergencyCase.objects.filter(
        status__in=["WAITING", "TRIAGE", "UNDER_CARE", "OBSERVATION"]
    ).count()
    emergency_critical = EmergencyCase.objects.filter(
        status__in=["WAITING", "TRIAGE", "UNDER_CARE", "OBSERVATION"],
        triage_level__in=["RED", "ORANGE"],
    ).count()

    today_lab_orders = LaboratoryOrder.objects.filter(requested_at__date=today).count()
    pending_lab_orders = LaboratoryOrder.objects.filter(
        status__in=["REQUESTED", "RECEIVED", "COLLECTED", "PROCESSING"]
    ).count()
    completed_lab_orders = LaboratoryOrder.objects.filter(status="COMPLETED").count()
    pending_result_deliveries = LaboratoryResultDelivery.objects.filter(received=False).count()

    pending_verification_count = (
        LaboratoryOrderItem.objects.filter(verified=False)
        .filter(Q(result__isnull=False) | Q(result_numeric__isnull=False))
        .exclude(status__in=["CANCELLED", "REJECTED"])
        .count()
    )

    alerts = []
    if emergency_critical:
        alerts.append({
            "level": "danger",
            "icon": "🚨",
            "title": "حالات طوارئ حرجة",
            "count": emergency_critical,
            "text": "تحتاج متابعة عاجلة.",
            "url": reverse("emergency:dashboard"),
        })

    if pending_verification_count:
        alerts.append({
            "level": "warning",
            "icon": "🧪",
            "title": "نتائج بانتظار الاعتماد",
            "count": pending_verification_count,
            "text": "تم إدخال النتائج ولم يتم اعتمادها بعد.",
            "url": reverse("laboratory:dashboard"),
        })

    context = {
        "now": timezone.localtime(),
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
        "occupied_beds": occupied_beds,
        "available_beds": available_beds,
        "reserved_beds": reserved_beds,
        "maintenance_beds": maintenance_beds,
        "operational_beds": operational_beds,
        "bed_occupancy_percent": bed_occupancy_percent,
        "emergency_active": emergency_active,
        "emergency_critical": emergency_critical,
        "today_lab_orders": today_lab_orders,
        "pending_lab_orders": pending_lab_orders,
        "completed_lab_orders": completed_lab_orders,
        "pending_verification_count": pending_verification_count,
        "pending_result_deliveries": pending_result_deliveries,
        "alerts": alerts,
    }
    return render(request, "accounts/dashboard.html", context)


def login_view(request):
    """صفحة تسجيل الدخول للنظام."""
    if request.user.is_authenticated:
        try:
            if request.user.staff_profile.is_active:
                return redirect("accounts:dashboard")
        except StaffProfile.DoesNotExist:
            pass

    login_users = (
        User.objects.filter(is_active=True)
        .filter(staff_profile__is_active=True)
        .select_related("staff_profile", "staff_profile__department")
        .order_by("staff_profile__full_name", "username")
    )

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""

        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_active:
            try:
                if not user.staff_profile.is_active:
                    messages.error(request, "حساب الموظف غير فعال.")
                    return render(request, "accounts/login.html", {"login_users": login_users})
            except StaffProfile.DoesNotExist:
                messages.error(request, "هذا الحساب ليس مرتبطًا بملف موظف صالح.")
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
    query = (request.GET.get("q") or "").strip()
    role = (request.GET.get("role") or "").strip()
    department_id = (request.GET.get("department") or "").strip()

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
    query = (request.GET.get("q") or "").strip()
    role = (request.GET.get("role") or "").strip()
    department_id = (request.GET.get("department") or "").strip()

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
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""
        password2 = request.POST.get("password2") or ""
        employee_number = (request.POST.get("employee_number") or "").strip()
        full_name = (request.POST.get("full_name") or "").strip()
        role = request.POST.get("role", "OTHER")
        department_id = request.POST.get("department") or None
        phone = (request.POST.get("phone") or "").strip()

        valid_roles = {value for value, _label in StaffProfile.ROLE_CHOICES}
        if role not in valid_roles:
            messages.error(request, "الدور الوظيفي المحدد غير صالح.")
        elif not username or not password or not employee_number or not full_name:
            messages.error(request, "يرجى تعبئة جميع الحقول المطلوبة.")
        elif password != password2:
            messages.error(request, "كلمتا المرور غير متطابقتين.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "اسم المستخدم موجود مسبقًا.")
        elif StaffProfile.objects.filter(employee_number=employee_number).exists():
            messages.error(request, "الرقم الوظيفي موجود مسبقًا.")
        else:
            if department_id and not Department.objects.filter(pk=department_id, is_active=True).exists():
                messages.error(request, "القسم المحدد غير موجود أو غير نشط.")
            else:
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

    return render(request, "accounts/user_form.html", {
        "departments": departments,
        "roles": StaffProfile.ROLE_CHOICES,
    })


@login_required
@user_passes_test(is_admin)
def user_edit(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    profile, _created = StaffProfile.objects.get_or_create(
        user=user,
        defaults={
            "employee_number": f"EMP-{user.id}",
            "full_name": user.get_full_name() or user.username,
            "role": "OTHER",
        },
    )
    departments = Department.objects.filter(is_active=True).order_by("name_ar")

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        employee_number = (request.POST.get("employee_number") or "").strip()
        full_name = (request.POST.get("full_name") or "").strip()
        role = request.POST.get("role", "OTHER")
        department_id = request.POST.get("department") or None
        phone = (request.POST.get("phone") or "").strip()
        new_password = request.POST.get("password") or ""
        new_password2 = request.POST.get("password2") or ""

        if not username or not employee_number or not full_name:
            messages.error(request, "يرجى تعبئة الحقول المطلوبة.")
        elif User.objects.exclude(pk=user.pk).filter(username=username).exists():
            messages.error(request, "اسم المستخدم مستخدم من حساب آخر.")
        elif StaffProfile.objects.exclude(pk=profile.pk).filter(employee_number=employee_number).exists():
            messages.error(request, "الرقم الوظيفي مستخدم من موظف آخر.")
        elif new_password and new_password != new_password2:
            messages.error(request, "كلمتا المرور غير متطابقتين.")
        else:
            if new_password:
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

    return render(request, "accounts/user_form.html", {
        "edit_mode": True,
        "user_obj": user,
        "profile": profile,
        "departments": departments,
        "roles": StaffProfile.ROLE_CHOICES,
    })


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

    state = "تم تفعيل المستخدم." if user.is_active else "تم تعط��ل المستخدم."
    messages.success(request, state)
    return redirect("accounts:user_list")


@login_required
@user_passes_test(is_admin)
def user_permissions(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)
    profile, _created = StaffProfile.objects.get_or_create(
        user=target_user,
        defaults={
            "employee_number": f"EMP-{target_user.id:05d}",
            "full_name": target_user.get_full_name() or target_user.username,
            "role": "OTHER",
        },
    )

    if request.method == "POST":
        valid_permissions = {
            permission
            for group in PERMISSION_GROUPS.values()
            for permission, _label in group["permissions"]
        }
        allowed = request.POST.getlist("allowed_permissions")
        denied = request.POST.getlist("denied_permissions")

        profile.custom_permissions = [
            permission for permission in allowed if permission in valid_permissions
        ]
        profile.denied_permissions = [
            permission for permission in denied if permission in valid_permissions
        ]
        profile.custom_permissions = [
            permission
            for permission in profile.custom_permissions
            if permission not in profile.denied_permissions
        ]
        profile.save(update_fields=["custom_permissions", "denied_permissions", "updated_at"])
        messages.success(request, f"تم حفظ صلاحيات المستخدم {target_user.username} بنجاح.")
        return redirect("accounts:user_permissions", user_id=target_user.id)

    custom_permissions = set(profile.custom_permissions or [])
    denied_permissions = set(profile.denied_permissions or [])
    role = profile.role
    role_permissions = set(ROLE_PERMISSIONS.get(role, set()))
    effective_permissions = (role_permissions | custom_permissions) - denied_permissions

    context = {
        "target_user": target_user,
        "profile": profile,
        "permission_groups": PERMISSION_GROUPS,
        "custom_permissions": custom_permissions,
        "denied_permissions": denied_permissions,
        "role_permissions": role_permissions,
        "effective_permissions": effective_permissions,
        "is_full_access": "*" in role_permissions,
    }
    return render(request, "accounts/user_permissions.html", context)
