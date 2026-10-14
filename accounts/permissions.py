from django.core.exceptions import ObjectDoesNotExist


# ============================================================
# أدوار المستخدمين
# الدور = الوظيفة
# القسم = مكان العمل
# الصلاحية = ما يستطيع المستخدم فعله
# ============================================================

ROLE_ACCESS = {
    "ADMIN": {
        "patients", "inpatient", "emergency", "laboratory",
        "doctors", "inventory", "pharmacy", "surgery",
        "reception", "billing", "accounts", "nursing",
        "departments", "blood_bank", "radiology", "reports", "system_settings",
    },

    "MANAGER": {
        "patients", "inpatient", "emergency", "laboratory",
        "doctors", "inventory", "pharmacy", "surgery",
        "reception", "billing", "accounts", "nursing",
        "departments", "blood_bank", "radiology", "reports", "system_settings",
    },

    "RECEPTION": {
        "patients", "reception", "doctors", "departments",
    },

    "DOCTOR": {'patients', 'inpatient', 'emergency', 'laboratory', 'doctors', 'pharmacy', 'surgery', 'reception', 'radiology', 'departments'},

    "LAB": {
        "patients", "laboratory",
    },

    "RADIOLOGY": {'patients', 'radiology', 'departments'},

    "PHARMACY": {'patients', 'pharmacy', 'inventory', 'departments'},

    "NURSING": {'patients', 'emergency', 'inpatient', 'nursing', 'departments'},

    "EMERGENCY": {'patients', 'laboratory', 'emergency', 'nursing', 'radiology', 'pharmacy', 'departments'},

    "INPATIENT": {'patients', 'inpatient', 'laboratory', 'nursing', 'radiology', 'pharmacy', 'departments'},

    "SURGERY": {'patients', 'laboratory', 'blood_bank', 'radiology', 'pharmacy', 'surgery', 'departments'},

    "BLOOD_BANK": {'laboratory', 'patients', 'blood_bank', 'departments'},

    "BILLING": {'billing', 'departments', 'patients', 'reception'},

    "INVENTORY": {'departments', 'inventory', 'laboratory', 'pharmacy'},

    "OTHER": {'departments'},
}


# ============================================================
# الصلاحيات التفصيلية
# ============================================================

ROLE_PERMISSIONS = {'ADMIN': {'*'}, 'MANAGER': {'*'}, 'RECEPTION': { 'patients.profile', 'patients.search', 'patients.visits.create', 'departments.view', 'patients.edit', 'patients.create', 'reception.create', 'reception.view', 'patients.view', 'doctors.view', 'reception.edit'}, 'DOCTOR': {'departments.view', 'radiology.orders.view', 'patients.edit', 'laboratory.view', 'radiology.reports.view', 'inpatient.view', 'laboratory.orders.view', 'patients.create', 'emergency.view', 'radiology.orders.create', 'reception.view', 'laboratory.create_order', 'laboratory.reports.view', 'patients.view', 'surgery.view', 'doctors.view', 'pharmacy.view', 'radiology.view'}, 'LAB': {'laboratory.reports.pdf', 'laboratory.sample.receive', 'laboratory.orders.view', 'laboratory.results.enter', 'laboratory.results.verify', 'patients.view', 'laboratory.tests.create', 'laboratory.devices.create', 'laboratory.tests.toggle', 'laboratory.devices.edit', 'laboratory.create_order', 'laboratory.tests.delete', 'laboratory.devices.toggle', 'laboratory.reagents.view', 'laboratory.inventory.view', 'laboratory.reagents.create', 'laboratory.inventory.create', 'laboratory.devices.view', 'laboratory.reports.view', 'laboratory.tests.view', 'laboratory.view', 'laboratory.reagents.toggle', 'laboratory.reagents.edit', 'laboratory.report_settings', 'laboratory.inventory.movement', 'laboratory.tests.edit'}, 'RADIOLOGY': {'departments.view', 'radiology.orders.view', 'radiology.results.edit', 'radiology.reports.view', 'radiology.orders.create', 'patients.view', 'radiology.exam_types.manage', 'radiology.orders.status', 'radiology.results.enter', 'radiology.view'}, 'PHARMACY': { 'pharmacy.dispense', 'pharmacy.inventory.movement', 'pharmacy.inventory.view', 'pharmacy.prescriptions.view', 'inventory.view', 'departments.view', 'inventory.create', 'pharmacy.create', 'pharmacy.prescriptions.edit', 'pharmacy.prescriptions.create', 'patients.view', 'pharmacy.view', 'inventory.movement', 'pharmacy.edit'}, 'NURSING': { 'nursing.notes.create', 'nursing.vitals.enter', 'departments.view', 'laboratory.view', 'inpatient.view', 'emergency.view', 'nursing.assessment.create', 'nursing.care_plan.create', 'nursing.medications.create', 'patients.view', 'nursing.view', 'radiology.view'}, 'EMERGENCY': {'departments.view', 'radiology.orders.view', 'laboratory.view', 'radiology.reports.view', 'inpatient.view', 'laboratory.orders.view', 'emergency.view', 'radiology.orders.create', 'laboratory.create_order', 'laboratory.reports.view', 'patients.view', 'pharmacy.view', 'nursing.view', 'radiology.view'}, 'INPATIENT': {'departments.view', 'radiology.orders.view', 'laboratory.view', 'radiology.reports.view', 'inpatient.view', 'laboratory.orders.view', 'radiology.orders.create', 'laboratory.create_order', 'laboratory.reports.view', 'patients.view', 'pharmacy.view', 'nursing.view', 'radiology.view'}, 'SURGERY': { 'surgery.create',  'surgery.edit', 'blood_bank.view', 'radiology.orders.view', 'departments.view', 'laboratory.view', 'surgery.status', 'surgery.types.manage', 'radiology.reports.view', 'laboratory.orders.view', 'radiology.orders.create', 'laboratory.create_order', 'surgery.view', 'patients.view', 'laboratory.reports.view', 'pharmacy.view', 'surgery.procedures.create', 'surgery.team.create', 'surgery.postoperative_notes.create', 'radiology.view'}, 'BLOOD_BANK': { 'blood_bank.donors.view', 'blood_bank.issue', 'blood_bank.receive', 'blood_bank.units.view', 'blood_bank.view', 'departments.view', 'laboratory.view', 'blood_bank.requests.create', 'blood_bank.donors.create', 'blood_bank.crossmatch', 'laboratory.orders.view', 'blood_bank.donors.edit', 'laboratory.reports.view', 'patients.view', 'blood_bank.units.create', 'blood_bank.transfusion'}, 'BILLING': { 'billing.payment', 'departments.view', 'billing.create', 'billing.items.delete', 'billing.view', 'reception.view', 'billing.items.create', 'patients.view', 'billing.edit', 'billing.status'}, 'INVENTORY': {'departments.view', 'inventory.view', 'inventory.create', 'laboratory.view', 'laboratory.inventory.movement', 'pharmacy.view', 'laboratory.inventory.view', 'inventory.movement', 'laboratory.inventory.create'}, 'OTHER': {'departments.view'}}


# ============================================================
# Prefixes الخاصة بالتطبيقات
# ============================================================


# ============================================================
# القائمة المركزية لصلاحيات نظام HIS / LIS
# ============================================================

PERMISSION_GROUPS = {'patients': {'title': 'المرضى والملفات الطبية', 'permissions': [('patients.view', 'عرض المرضى'), ('patients.create', 'إضافة مريض'), ('patients.edit', 'تعديل بيانات المريض'), ('patients.search', 'البحث عن المرضى'), ('patients.profile', 'عرض الملف الطبي'), ('patients.visits.view', 'عرض زيارات المريض'), ('patients.visits.create', 'إنشاء زيارة'), ('patients.visits.edit', 'تعديل الزيارة')]}, 'reception': {'title': 'الاستقبال والمواعيد', 'permissions': [('reception.view', 'عرض الاستقبال'), ('reception.create', 'إنشاء تسجيل'), ('reception.edit', 'تعديل التسجيل'), ('reception.appointments.view', 'عرض المواعيد'), ('reception.appointments.create', 'إنشاء موعد'), ('reception.appointments.edit', 'تعديل الموعد'), ('reception.transfer', 'تحويل المريض إلى قسم'), ('reception.print_card', 'طباعة بطاقة المريض')]}, 'laboratory': {'title': 'المختبر', 'permissions': [('laboratory.view', 'عرض المختبر'), ('laboratory.create_order', 'إنشاء طلب فحص'), ('laboratory.orders.view', 'عرض طلبات المختبر'), ('laboratory.sample.receive', 'استلام العينات'), ('laboratory.results.enter', 'إدخال النتائج'), ('laboratory.results.edit', 'تعديل النتائج'), ('laboratory.results.verify', 'مراجعة واعتماد النتائج'), ('laboratory.results.cancel', 'إلغاء نتيجة'), ('laboratory.reports.view', 'عرض التقارير'), ('laboratory.reports.print', 'طباعة التقارير'), ('laboratory.reports.pdf', 'تصدير التقرير PDF'), ('laboratory.reports.send', 'إرسال التقرير للطبيب أو القسم'), ('laboratory.report_settings', 'إعدادات تقارير المختبر')]}, 'tests': {'title': 'إدارة الفحوصات', 'permissions': [('laboratory.tests.view', 'عرض الفحوصات'), ('laboratory.tests.create', 'إضافة فحص'), ('laboratory.tests.edit', 'تعديل فحص'), ('laboratory.tests.toggle', 'تفعيل أو تعطيل فحص'), ('laboratory.tests.delete', 'حذف فحص')]}, 'devices': {'title': 'أجهزة المختبر', 'permissions': [('laboratory.devices.view', 'عرض الأجهزة'), ('laboratory.devices.create', 'إضافة جهاز'), ('laboratory.devices.edit', 'تعديل جهاز'), ('laboratory.devices.toggle', 'تفعيل أو تعطيل جهاز')]}, 'reagents': {'title': 'الكواشف والمحاليل', 'permissions': [('laboratory.reagents.view', 'عرض الكواشف'), ('laboratory.reagents.create', 'إضافة كاشف'), ('laboratory.reagents.edit', 'تعديل كاشف'), ('laboratory.reagents.toggle', 'تفعيل أو تعطيل كاشف')]}, 'lab_inventory': {'title': 'مخزون المختبر', 'permissions': [('laboratory.inventory.view', 'عرض مخزون المختبر'), ('laboratory.inventory.create', 'إضافة مخزون المختبر'), ('laboratory.inventory.movement', 'حركة مخزون المختبر')]}, 'radiology': {'title': 'الأشعة والتصوير الطبي', 'permissions': [('radiology.view', 'عرض الأشعة'), ('radiology.orders.view', 'عرض طلبات الأشعة'), ('radiology.results.enter', 'إدخال نتائج الأشعة'), ('radiology.results.edit', 'تعديل نتائج الأشعة'), ('radiology.reports.view', 'عرض تقارير الأشعة'), ('radiology.reports.print', 'طباعة تقارير الأشعة'), ('radiology.orders.create', 'إنشاء طلب أشعة'), ('radiology.orders.status', 'تحديث حالة طلب الأشعة'), ('radiology.exam_types.manage', 'إدارة أنواع الأشعة')]}, 'pharmacy': {'title': 'الصيدلية', 'permissions': [('pharmacy.view', 'عرض الصيدلية'), ('pharmacy.create', 'إضافة دواء'), ('pharmacy.edit', 'تعديل دواء'), ('pharmacy.prescriptions.view', 'عرض الوصفات'), ('pharmacy.dispense', 'صرف الدواء'), ('pharmacy.inventory.view', 'عرض مخزون الصيدلية'), ('pharmacy.inventory.movement', 'حركة مخزون الصيدلية'), ('pharmacy.prescriptions.create', 'إنشاء وصفة'), ('pharmacy.prescriptions.edit', 'تعديل الوصفة')]}, 'nursing': {'title': 'التمريض', 'permissions': [('nursing.view', 'عرض التمريض'), ('nursing.vitals.enter', 'تسجيل العلامات الحيوية'), ('nursing.notes.create', 'إضافة ملاحظات تمريضية'), ('nursing.assessment.create', 'إنشاء تقييم تمريضي'), ('nursing.medications.create', 'إضافة دواء تمريضي'), ('nursing.care_plan.create', 'إنشاء خطة رعاية')]}, 'emergency': {'title': 'الطوارئ', 'permissions': [('emergency.view', 'عرض الطوارئ'), ('emergency.create', 'تسجيل حالة طوارئ'), ('emergency.edit', 'تعديل حالة الطوارئ')]}, 'inpatient': {'title': 'التنويم', 'permissions': [('inpatient.view', 'عرض التنويم'), ('inpatient.admission.create', 'تنويم مريض'), ('inpatient.admission.edit', 'تعديل بيانات التنويم'), ('inpatient.discharge', 'خروج المريض'), ('inpatient.rooms.view', 'عرض الغرف'), ('inpatient.rooms.create', 'إضافة غرفة'), ('inpatient.rooms.edit', 'تعديل الغرف'), ('inpatient.beds.view', 'عرض الأسرة'), ('inpatient.beds.create', 'إضافة سرير'), ('inpatient.beds.edit', 'تعديل الأسرة')]}, 'surgery': {'title': 'العمليات والجراحة', 'permissions': [('surgery.view', 'عرض العمليات'), ('surgery.schedule', 'جدولة عملية'), ('surgery.create', 'إنشاء عملية'), ('surgery.edit', 'تعديل العملية'), ('surgery.status', 'تحديث حالة العملية'), ('surgery.procedures.create', 'إضافة إجراء للعملية'), ('surgery.team.create', 'إضافة عضو لفريق العملية'), ('surgery.postoperative_notes.create', 'إضافة ملاحظة بعد العملية'), ('surgery.types.manage', 'إدارة أنواع العمليات')]}, 'blood_bank': {'title': 'بنك الدم', 'permissions': [('blood_bank.view', 'عرض بنك الدم'), ('blood_bank.donors.view', 'عرض المتبرعين'), ('blood_bank.units.view', 'عرض وحدات الدم'), ('blood_bank.issue', 'صرف وحدة دم'), ('blood_bank.receive', 'استلام وحدة دم'), ('blood_bank.donors.create', 'إضافة متبرع'), ('blood_bank.donors.edit', 'تعديل بيانات المتبرع'), ('blood_bank.units.create', 'إضافة وحدة دم'), ('blood_bank.requests.create', 'إنشاء طلب دم'), ('blood_bank.crossmatch', 'إجراء المطابقة'), ('blood_bank.transfusion', 'إدارة نقل الدم')]}, 'billing': {'title': 'المالية والفوترة', 'permissions': [('billing.view', 'عرض الحسابات'), ('billing.create', 'إنشاء فاتورة'), ('billing.edit', 'تعديل الفاتورة'), ('billing.payment', 'تسجيل دفعة'), ('billing.refund', 'إجراء استرداد'), ('billing.items.create', 'إضافة بند للفاتورة'), ('billing.items.delete', 'حذف بند من الفاتورة'), ('billing.status', 'تحديث حالة الفاتورة')]}, 'inventory': {'title': 'المخزون العام', 'permissions': [('inventory.view', 'عرض المخزون'), ('inventory.create', 'إضافة مخزون'), ('inventory.movement', 'حركة المخزون')]}, 'doctors': {'title': 'الأطباء والأقسام', 'permissions': [('doctors.view', 'عرض الأطباء'), ('doctors.create', 'إضافة طبيب'), ('doctors.edit', 'تعديل بيانات الطبيب'), ('departments.view', 'عرض الأقسام'), ('departments.create', 'إضافة قسم'), ('departments.edit', 'تعديل القسم'), ('departments.toggle', 'تفعيل أو تعطيل القسم')]}, 'users': {'title': 'المستخدمون والصلاحيات', 'permissions': [('accounts.view', 'عرض المستخدمين'), ('accounts.create', 'إضافة مستخدم'), ('accounts.edit', 'تعديل المستخدم'), ('accounts.toggle', 'تفعيل أو تعطيل المستخدم'), ('accounts.permissions', 'إدارة صلاحيات المستخدم')]}}

APP_PREFIXES = {
    "reports": "/reports/",
    "system_settings": "/system-settings/",
    "patients": "/patients/",
    "doctors": "/doctors/",
    "laboratory": "/laboratory/",
    "radiology": "/radiology/",
    "pharmacy": "/pharmacy/",
    "nursing": "/nursing/",
    "emergency": "/emergency/",
    "inpatient": "/inpatient/",
    "surgery": "/surgery/",
    "blood_bank": "/blood-bank/",
    "billing": "/billing/",
    "inventory": "/inventory/",
    "reception": "/reception/",
    "accounts": "/accounts/",
    "departments": "/departments/",
}


# ============================================================
# الحصول على الملف الوظيفي
# ============================================================

def get_staff_profile(user):
    if not user or not user.is_authenticated:
        return None

    try:
        return user.staff_profile
    except ObjectDoesNotExist:
        return None


def get_user_role(user):
    if not user or not user.is_authenticated:
        return None

    if user.is_superuser:
        return "ADMIN"

    profile = get_staff_profile(user)

    if not profile:
        return None

    return profile.role


def get_user_department(user):
    profile = get_staff_profile(user)

    if not profile:
        return None

    return profile.department


# ============================================================
# صلاحية الوصول إلى التطبيق
# ============================================================

def get_user_custom_permissions(user):
    """الصلاحيات الإضافية الممنوحة مباشرة للمستخدم."""
    profile = get_staff_profile(user)

    if not profile:
        return set()

    permissions = profile.custom_permissions or []

    if not isinstance(permissions, list):
        return set()

    return {
        str(permission).strip()
        for permission in permissions
        if str(permission).strip()
    }


def get_user_denied_permissions(user):
    """الصلاحيات الممنوعة مباشرة للمستخدم."""
    profile = get_staff_profile(user)

    if not profile:
        return set()

    permissions = profile.denied_permissions or []

    if not isinstance(permissions, list):
        return set()

    return {
        str(permission).strip()
        for permission in permissions
        if str(permission).strip()
    }


def get_effective_permissions(user):
    if not user or not user.is_authenticated:
        return set()

    if user.is_superuser:
        return {"*"}

    role = get_user_role(user)

    role_permissions = set(ROLE_PERMISSIONS.get(role, set()))
    custom_permissions = get_user_custom_permissions(user)
    denied_permissions = get_user_denied_permissions(user)

    effective = role_permissions | custom_permissions

    # إذا كان الدور لديه "*" فهذا يعني كل الصلاحيات.
    # الصلاحيات الموجودة في denied_permissions تبقى ممنوعة.
    if "*" in effective:
        return {"*"} | custom_permissions

    effective.difference_update(denied_permissions)

    return effective


def user_has_access(user, app_name):
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    role = get_user_role(user)
    if not role:
        return False

    denied_permissions = get_user_denied_permissions(user)

    # منع الوصول الكامل للتطبيق إذا تم منع التطبيق نفسه.
    if app_name in denied_permissions:
        return False

    role_apps = ROLE_ACCESS.get(role, set())
    effective = get_effective_permissions(user)

    # "*" = وصول شامل، لكن مع احترام denied_permissions.
    if "*" in effective:
        app_prefix = f"{app_name}."
        if any(
            permission.startswith(app_prefix)
            for permission in denied_permissions
        ):
            # لا نمنع دخول التطبيق بسبب منع عملية واحدة فقط.
            return True
        return True

    if app_name in role_apps:
        return True

    app_prefix = f"{app_name}."
    return any(
        permission.startswith(app_prefix)
        for permission in effective
    )


def user_has_permission(user, permission):
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    denied_permissions = get_user_denied_permissions(user)

    # المنع له الأولوية على "*" والصلاحيات المخصصة.
    if permission in denied_permissions:
        return False

    effective = get_effective_permissions(user)

    if "*" in effective:
        return True

    return permission in effective


def user_has_any_permission(user, permissions):
    return any(
        user_has_permission(user, permission)
        for permission in permissions
    )


def user_has_all_permissions(user, permissions):
    return all(
        user_has_permission(user, permission)
        for permission in permissions
    )


def user_has_role(user, *roles):
    role = get_user_role(user)

    # ADMIN يمكن اعتباره صاحب صلاحية إدارية عامة.
    if role == "ADMIN":
        return True

    return role in roles

def get_user_access_info(user):
    role = get_user_role(user)
    department = get_user_department(user)

    return {
        "role": role,
        "department": department,
        "department_id": department.id if department else None,
        "department_code": department.code if department else None,
        "is_admin": role in {"ADMIN", "MANAGER"},
        "is_superuser": bool(
            user and user.is_authenticated and user.is_superuser
        ),
        "apps": sorted(ROLE_ACCESS.get(role, set())),
        "permissions": sorted(ROLE_PERMISSIONS.get(role, set())),
    }
