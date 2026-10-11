from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .models import SystemSetting


# ============================================================
# SYSTEM SETTINGS — ACCESS CONTROL
# ============================================================

def is_system_admin(user):
    """
    الوصول إلى إعدادات النظام المركزية:
    - Superuser
    - الدور ADMIN فقط

    MANAGER لا يدخل إلى هذه الصفحة حتى لو كان لديه
    صلاحيات HIS/LIS كاملة.
    """
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    try:
        profile = user.staff_profile
    except Exception:
        return False

    return (
        profile is not None
        and profile.is_active
        and profile.role == "ADMIN"
    )


# ============================================================
# SYSTEM SETTINGS DASHBOARD
# ============================================================

@login_required
def settings_dashboard(request):
    """
    لوحة إعدادات النظام المركزية.
    """

    if not is_system_admin(request.user):
        messages.error(
            request,
            "ليس لديك صلاحية للوصول إلى إعدادات النظام المركزية."
        )
        return redirect("/accounts/")

    categories = [
        ("HOSPITAL", "🏥", "بيانات المستشفى"),
        ("NUMBERING", "🔢", "الترقيم وأرقام الملفات"),
        ("CENTERS", "🏥", "مراكز النظام"),
        ("LABORATORY", "🧪", "إعدادات المختبر"),
        ("REPORTS", "📄", "إعدادات التقارير"),
        ("NOTIFICATIONS", "🔔", "الإشعارات"),
        ("BILLING", "💰", "الفوترة والمالية"),
        ("LOCALIZATION", "🌐", "اللغة والتاريخ"),
        ("SECURITY", "🔐", "الأمان"),
        ("BACKUP", "💾", "النسخ الاحتياطي"),
        ("MAINTENANCE", "🛠️", "الصيانة"),
    ]

    settings_by_category = {}

    for code, icon, title in categories:
        settings_by_category[code] = {
            "code": code,
            "icon": icon,
            "title": title,
            "items": SystemSetting.objects.filter(
                category=code,
                is_active=True,
            ),
        }

    context = {
        "categories": categories,
        "settings_by_category": settings_by_category,
        "total_settings": SystemSetting.objects.count(),
    }

    return render(
        request,
        "system_settings/dashboard.html",
        context,
    )


# ============================================================
# UPDATE SETTINGS
# ============================================================

@login_required
def update_settings(request):
    """
    حفظ إعدادات النظام.

    التحديث يتم فقط للإعدادات الموجودة مسبقًا في قاعدة البيانات.
    لا يتم إنشاء مفاتيح جديدة من POST.
    """

    if not is_system_admin(request.user):
        messages.error(
            request,
            "ليس لديك صلاحية لتعديل إعدادات النظام."
        )
        return redirect("/accounts/")

    if request.method != "POST":
        return redirect("system_settings:dashboard")

    updated_count = 0

    for setting in SystemSetting.objects.filter(is_active=True):
        field_name = f"setting_{setting.id}"

        # Boolean settings:
        # checkbox موجود = true
        # checkbox غير موجود = false
        if setting.value in ("true", "false"):
            new_value = "true" if field_name in request.POST else "false"

        else:
            if field_name not in request.POST:
                continue

            new_value = request.POST.get(field_name, "").strip()

        if setting.value != new_value:
            setting.value = new_value
            setting.save(update_fields=["value", "updated_at"])
            updated_count += 1

    if updated_count:
        messages.success(
            request,
            f"تم حفظ {updated_count} إعداد بنجاح."
        )
    else:
        messages.info(
            request,
            "لا توجد تغييرات جديدة لحفظها."
        )

    return redirect("system_settings:dashboard")
