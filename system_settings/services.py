"""
Central System Settings Service
================================

طبقة موحدة وآمنة لقراءة إعدادات النظام.

مبادئ هذه الطبقة:
- READ ONLY
- لا تنشئ إعدادات تلقائيًا.
- لا تعدل قاعدة البيانات.
- تعيد default عند عدم وجود المفتاح.
- توفر تحويلًا آمنًا إلى bool / int.
"""

from .models import SystemSetting


TRUE_VALUES = {
    "true",
    "1",
    "yes",
    "on",
    "enabled",
    "active",
}

FALSE_VALUES = {
    "false",
    "0",
    "no",
    "off",
    "disabled",
    "inactive",
}


def get_setting(key, default=""):
    """
    قراءة إعداد نصي.

    إذا لم يوجد المفتاح أو كان غير فعال:
    يتم إرجاع default.
    """
    try:
        setting = SystemSetting.objects.filter(
            key=key,
            is_active=True,
        ).only("value").first()

        if setting is None:
            return default

        return setting.value

    except Exception:
        return default


def get_bool_setting(key, default=False):
    """
    قراءة إعداد Boolean بشكل آمن.
    """
    value = get_setting(key, None)

    if value is None:
        return default

    value = str(value).strip().lower()

    if value in TRUE_VALUES:
        return True

    if value in FALSE_VALUES:
        return False

    return default


def get_int_setting(key, default=0):
    """
    قراءة إعداد رقمي بشكل آمن.
    """
    value = get_setting(key, None)

    if value is None:
        return default

    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


# ============================================================
# Hospital Identity
# ============================================================

def get_hospital_identity(fallback=None):
    """
    قراءة هوية المستشفى المركزية مع Fallback آمن.

    الأولوية:
    1) SystemSetting المركزي إذا كانت القيمة موجودة.
    2) LaboratoryReportSettings الحالية عند عدم وجود
       قيمة مركزية.

    هذه الدالة لا تعدل قاعدة البيانات.
    """

    if fallback is None:
        fallback = {}

    result = {
        "name_ar": get_setting(
            "hospital.name_ar",
            fallback.get("name_ar", ""),
        ),
        "name_en": get_setting(
            "hospital.name_en",
            fallback.get("name_en", ""),
        ),
        "address": get_setting(
            "hospital.address",
            fallback.get("address", ""),
        ),
        "phone": get_setting(
            "hospital.phone",
            fallback.get("phone", ""),
        ),
        "email": get_setting(
            "hospital.email",
            fallback.get("email", ""),
        ),
    }

    # إذا كان المفتاح موجودًا لكن قيمته فارغة،
    # نستخدم القيمة القديمة الموجودة في إعدادات التقرير.
    for key in result:
        if not str(result[key] or "").strip():
            result[key] = fallback.get(key, "")

    return result

# ============================================================
# PHASE 8.4.3 — CENTRAL NUMBERING SERVICE
# ============================================================

def _normalize_prefix(prefix):
    """
    Normalize a numbering prefix.
    """
    return str(prefix or "").strip().upper().replace(" ", "-")


def _safe_positive_int(value, default=1):
    """
    Convert a value to a positive integer safely.
    """
    try:
        number = int(str(value).strip())
        return number if number > 0 else default
    except (TypeError, ValueError):
        return default


def _extract_number(value, prefix=""):
    """
    Extract the numeric portion from existing identifiers.

    Supports examples such as:
        77
        P-000078
        P000078
        LAB-000053
        LAB-53

    Returns 0 when no valid number is found.
    """
    import re

    text = str(value or "").strip().upper()
    if not text:
        return 0

    prefix = _normalize_prefix(prefix)

    if prefix:
        pattern = rf"^{re.escape(prefix)}[-_ ]*(\d+)$"
        match = re.match(pattern, text)
        if match:
            try:
                return int(match.group(1))
            except (TypeError, ValueError):
                return 0

    match = re.search(r"(\d+)$", text)
    if match:
        try:
            return int(match.group(1))
        except (TypeError, ValueError):
            return 0

    return 0


def _format_number(prefix, number):
    """
    Format a generated identifier.

    Example:
        P + 78 -> P-000078
        LAB + 53 -> LAB-000053
    """
    prefix = _normalize_prefix(prefix)

    if prefix:
        return f"{prefix}-{int(number):06d}"

    return str(int(number))


def _next_number_from_queryset(queryset, field_name, prefix, start=1):
    """
    Find the next available numeric sequence from an existing queryset.
    Existing records are never modified.
    """
    maximum = 0

    for value in queryset.values_list(field_name, flat=True):
        current = _extract_number(value, prefix)

        if current > maximum:
            maximum = current

    candidate = max(maximum + 1, start)

    while queryset.filter(**{field_name: _format_number(prefix, candidate)}).exists():
        candidate += 1

    return _format_number(prefix, candidate)


def get_next_patient_number():
    """
    Generate the next patient number according to System Settings.

    AUTO:
        Generate centrally.

    MANUAL:
        Return None so the calling form/view can require manual entry.
    """
    from patients.models import Patient

    mode = get_setting("numbering.patient_mode", "AUTO").strip().upper()

    if mode == "MANUAL":
        return None

    prefix = get_setting("numbering.patient_prefix", "P")
    start = _safe_positive_int(
        get_setting("numbering.patient_start", "1"),
        1,
    )

    return _next_number_from_queryset(
        Patient.objects.all(),
        "patient_number",
        prefix,
        start,
    )


def get_next_visit_number():
    """
    Generate the next visit number.
    """
    from patients.models import Visit

    prefix = get_setting("numbering.visit_prefix", "V")

    return _next_number_from_queryset(
        Visit.objects.all(),
        "visit_number",
        prefix,
        1,
    )


def get_next_lab_order_number():
    """
    Generate the next laboratory order number.
    """
    from laboratory.models import LaboratoryOrder

    prefix = get_setting("numbering.lab_order_prefix", "LAB")

    return _next_number_from_queryset(
        LaboratoryOrder.objects.all(),
        "order_number",
        prefix,
        1,
    )


def get_next_report_number():
    """
    Reports currently use the laboratory order number.
    This function intentionally does NOT create a separate report
    numbering sequence yet.
    """
    return get_next_lab_order_number()
