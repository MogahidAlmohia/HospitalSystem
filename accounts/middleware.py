from django.contrib import messages
from django.shortcuts import redirect

from .permissions import (
    APP_PREFIXES,
    get_user_role,
    user_has_access,
    user_has_permission,
)


PUBLIC_PREFIXES = (
    "/accounts/login/",
    "/accounts/logout/",
    "/admin/login/",
    "/static/",
    "/media/",
)


class RolePermissionMiddleware:
    """
    نظام الصلاحيات المركزي.

    يتحقق من:
    1. تسجيل الدخول
    2. حالة الحساب
    3. الوظيفة Role
    4. صلاحية التطبيق
    5. الصلاحية التفصيلية حسب الرابط
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # ========================================================
        # Django Admin
        # مستقل تمامًا عن صلاحيات HIS/LIS
        # ========================================================
        if path.startswith("/admin/"):
            return self.get_response(request)

        # الصفحات العامة
        if any(path.startswith(prefix) for prefix in PUBLIC_PREFIXES):
            return self.get_response(request)


        # المستخدم غير المسجل
        if not request.user.is_authenticated:
            return redirect("/accounts/login/")

        # المستخدم غير النشط
        if not request.user.is_active:
            messages.error(
                request,
                "حساب المستخدم غير نشط."
            )
            return redirect("/accounts/login/")

        # ملف الموظف المعطل يمنع الوصول حتى لو كان حساب Django فعالاً.
        if hasattr(request.user, "staff_profile") and not request.user.staff_profile.is_active:
            messages.error(
                request,
                "الملف الوظيفي للمستخدم غير نشط."
            )
            return redirect("/accounts/login/")

        # Superuser له صلاحية كاملة للنظام
        # يجب فحصه قبل StaffProfile حتى لا يحدث تعارض
        # إذا كان الدور الوظيفي في StaffProfile مختلفًا.
        if request.user.is_superuser:
            return self.get_response(request)

        role = get_user_role(request.user)

        # لا يوجد StaffProfile
        if not role:
            messages.error(
                request,
                "لا يوجد ملف وظيفي وصلاحيات مرتبطة بهذا الحساب."
            )
            return redirect("/accounts/login/")

        # تحديد التطبيق المطلوب
        requested_app = None

        for app_name, prefix in APP_PREFIXES.items():
            if path.startswith(prefix):
                requested_app = app_name
                break

        # الصفحات الرئيسية الخاصة بالحسابات
        # نسمح لـ /accounts/ و /accounts/login/ بالمرور إلى Views
        # حتى لا تحدث حلقة Redirect بين / و /accounts/.
        if path == "/accounts/" or path == "/accounts":
            return self.get_response(request)

        # الصفحة الرئيسية
        if requested_app is None:
            return self.get_response(request)

        # صلاحية التطبيق
        if not user_has_access(request.user, requested_app):
            messages.error(
                request,
                "ليس لديك صلاحية للوصول إلى هذه الصفحة حسب وظيفتك وقسمك."
            )
            return redirect("/")

        # الصلاحية التفصيلية
        required_permission = self.get_required_permission(path)

        if (
            required_permission
            and not user_has_permission(
                request.user,
                required_permission
            )
        ):
            messages.error(
                request,
                "ليس لديك الصلاحية لتنفيذ هذه العملية."
            )
            return redirect("/")

        return self.get_response(request)

    @staticmethod
    def get_required_permission(path):
        """
        ربط روابط النظام بالصلاحيات التفصيلية.

        ملاحظة:
        المنع الموجود في denied_permissions له الأولوية
        حتى لو كان المستخدم يملك صلاحية الدور أو "*".
        """

        # ============================================================
        # التنويم - Inpatient
        # ============================================================
        if path.startswith("/inpatient/"):

            # -------------------------
            # التنويم
            # -------------------------
            if path.startswith("/inpatient/admissions/create/"):
                return "inpatient.admission.create"

            if path.startswith("/inpatient/admissions/"):
                if path.endswith("/discharge/"):
                    return "inpatient.discharge"

                if path.endswith("/transfer/"):
                    return "inpatient.admission.edit"

                if path.endswith("/notes/create/"):
                    return "inpatient.admission.edit"

                if path.endswith("/vitals/create/"):
                    return "inpatient.admission.edit"

                if path.endswith("/edit/"):
                    return "inpatient.admission.edit"

                return "inpatient.view"

            # -------------------------
            # الغرف
            # -------------------------
            if path.startswith("/inpatient/rooms/"):
                if path.startswith("/inpatient/rooms/create/"):
                    return "inpatient.rooms.create"

                if path.endswith("/edit/"):
                    return "inpatient.rooms.edit"

                return "inpatient.rooms.view"

            # -------------------------
            # الأسرة
            # -------------------------
            if path.startswith("/inpatient/beds/"):
                if path.startswith("/inpatient/beds/create/"):
                    return "inpatient.beds.create"

                if path.endswith("/edit/"):
                    return "inpatient.beds.edit"

                return "inpatient.beds.view"

            # -------------------------
            # البحث
            # -------------------------
            if path.startswith("/inpatient/search/"):
                return "inpatient.view"

            return "inpatient.view"

        # ============================================================
        # إعدادات تقارير المختبر
        # ============================================================
        if path.startswith("/departments/create/"):
            return "departments.create"
        if path.startswith("/departments/"):
            if "/edit/" in path:
                return "departments.edit"
            if "/toggle/" in path:
                return "departments.toggle"
            return "departments.view"

        if path.startswith("/emergency/create/"):
            return "emergency.create"
        if path.startswith("/emergency/"):
            if "/edit/" in path:
                return "emergency.edit"
            return "emergency.view"

        if path.startswith("/laboratory/report-settings/"):
            return "laboratory.report_settings"

        # ============================================================
        # إدارة الفحوصات
        # ============================================================
        if path.startswith("/laboratory/tests/create/"):
            return "laboratory.tests.create"

        if path.startswith("/laboratory/tests/"):
            if "/edit/" in path:
                return "laboratory.tests.edit"

            if "/toggle/" in path:
                return "laboratory.tests.toggle"

            if "/delete/" in path:
                return "laboratory.tests.delete"

            return "laboratory.tests.view"

        # ============================================================
        # الأجهزة
        # ============================================================
        if path.startswith("/laboratory/devices/create/"):
            return "laboratory.devices.create"

        if path.startswith("/laboratory/devices/"):
            if "/edit/" in path:
                return "laboratory.devices.edit"

            if "/toggle/" in path:
                return "laboratory.devices.toggle"

            return "laboratory.devices.view"

        # ============================================================
        # الكواشف والمحاليل
        # ============================================================
        if path.startswith("/laboratory/reagents/create/"):
            return "laboratory.reagents.create"

        if path.startswith("/laboratory/reagents/"):
            if "/edit/" in path:
                return "laboratory.reagents.edit"

            if "/toggle/" in path:
                return "laboratory.reagents.toggle"

            return "laboratory.reagents.view"

        # ============================================================
        # مخزون المختبر
        # ============================================================
        if path.startswith("/laboratory/inventory/"):
            if "/create/" in path:
                return "laboratory.inventory.create"

            if "/movement/" in path:
                return "laboratory.inventory.movement"

            return "laboratory.inventory.view"

        # ============================================================
        # استقبال العينات
        # ============================================================
        if path.startswith("/laboratory/sample-reception/"):
            return "laboratory.sample.receive"

        # ============================================================
        # إنشاء طلب فحص
        # ============================================================
        if path.startswith("/laboratory/orders/create/"):
            return "laboratory.create_order"

        # ============================================================
        # طلبات المختبر والنتائج والتقارير
        # ============================================================
        if path.startswith("/laboratory/orders/"):

            # إلغاء النتيجة
            if path.endswith("/cancel/"):
                return "laboratory.results.cancel"

            # تعديل النتيجة
            if path.endswith("/results/edit/"):
                return "laboratory.results.edit"

            # إدخال النتائج
            if path.endswith("/results/"):
                return "laboratory.results.enter"

            # اعتماد النتيجة
            if path.endswith("/verify/"):
                return "laboratory.results.verify"

            # إرسال التقرير للطبيب أو القسم
            if path.endswith("/report/send/"):
                return "laboratory.reports.send"

            # تصدير PDF
            if path.endswith("/report/pdf/"):
                return "laboratory.reports.pdf"

            # طباعة التقرير
            if path.endswith("/report/print/"):
                return "laboratory.reports.print"

            # عرض التقرير
            if path.endswith("/report/"):
                return "laboratory.reports.view"

            # عرض الطلبات
            return "laboratory.orders.view"

        # ============================================================
        # الصفحات العامة للمختبر
        # ============================================================
        if path.startswith("/laboratory/"):
            return "laboratory.view"

        # لا توجد صلاحية تفصيلية محددة
        # ============================================================
        # Reception / Patients
        # ============================================================
        if path.startswith("/reception/patients/register/"):
            return "patients.create"

        if path.startswith("/reception/patients/search/"):
            return "patients.search"

        if path.startswith("/reception/patients/"):
            if "/visit/create/" in path:
                return "patients.visits.create"
            return "patients.profile"

        if path.startswith("/reception/"):
            return "reception.view"

        # ============================================================
        # Doctors
        # ============================================================
        if path.startswith("/doctors/create/"):
            return "doctors.create"

        if path.startswith("/doctors/"):
            if "/edit/" in path:
                return "doctors.edit"
            if "/toggle/" in path:
                return "doctors.edit"
            return "doctors.view"

        # ============================================================
        # Radiology
        # ============================================================
        if path.startswith("/radiology/orders/create/"):
            return "radiology.orders.create"

        if path.startswith("/radiology/orders/"):
            if path.endswith("/status/"):
                return "radiology.orders.status"

            if path.endswith("/report/"):
                return "radiology.results.enter"

            return "radiology.orders.view"

        if path.startswith("/radiology/exam-types/"):
            return "radiology.exam_types.manage"

        if path.startswith("/radiology/patients/"):
            return "radiology.orders.view"

        if path.startswith("/radiology/"):
            return "radiology.view"

        # ============================================================
        # Pharmacy
        # ============================================================
        if path.startswith("/pharmacy/prescriptions/create/"):
            return "pharmacy.prescriptions.create"

        if path.startswith("/pharmacy/prescriptions/"):
            if "/add-item/" in path:
                return "pharmacy.prescriptions.edit"

            if "/dispense/" in path:
                return "pharmacy.dispense"

            return "pharmacy.prescriptions.view"

        if path.startswith("/pharmacy/medicines/create/"):
            return "pharmacy.create"

        if path.startswith("/pharmacy/medicines/"):
            if "/edit/" in path:
                return "pharmacy.edit"
            return "pharmacy.view"

        if path.startswith("/pharmacy/stock/"):
            if "/receive/" in path or "/adjust/" in path:
                return "pharmacy.inventory.movement"
            if path.startswith("/pharmacy/stock/movements/"):
                return "pharmacy.inventory.movement"
            return "pharmacy.inventory.view"

        if path.startswith("/pharmacy/"):
            return "pharmacy.view"

        # ============================================================
        # Nursing
        # ============================================================
        if path.startswith("/nursing/assessments/create/"):
            return "nursing.assessment.create"

        if path.startswith("/nursing/vitals/create/"):
            return "nursing.vitals.enter"

        if path.startswith("/nursing/notes/create/"):
            return "nursing.notes.create"

        if path.startswith("/nursing/medications/create/"):
            return "nursing.medications.create"

        if path.startswith("/nursing/care-plans/create/"):
            return "nursing.care_plan.create"

        if path.startswith("/nursing/"):
            return "nursing.view"

        # ============================================================
        # Surgery
        # ============================================================
        if path.startswith("/surgery/orders/create/"):
            return "surgery.create"

        if path.startswith("/surgery/orders/"):
            if "/status/" in path:
                return "surgery.status"

            if "/procedures/create/" in path:
                return "surgery.procedures.create"

            if "/team/create/" in path:
                return "surgery.team.create"

            if "/postoperative-notes/create/" in path:
                return "surgery.postoperative_notes.create"

            if "/edit/" in path:
                return "surgery.edit"

            return "surgery.view"

        if path.startswith("/surgery/types/"):
            return "surgery.types.manage"

        if path.startswith("/surgery/patients/"):
            return "surgery.view"

        if path.startswith("/surgery/"):
            return "surgery.view"

        # ============================================================
        # Blood Bank
        # ============================================================
        if path.startswith("/blood_bank/donors/create/"):
            return "blood_bank.donors.create"

        if path.startswith("/blood_bank/donors/"):
            if "/edit/" in path:
                return "blood_bank.donors.edit"
            return "blood_bank.donors.view"

        if path.startswith("/blood_bank/units/create/"):
            return "blood_bank.units.create"

        if path.startswith("/blood_bank/units/"):
            return "blood_bank.units.view"

        if path.startswith("/blood_bank/requests/create/"):
            return "blood_bank.requests.create"

        if path.startswith("/blood_bank/requests/"):
            if "/issue/" in path:
                return "blood_bank.issue"

            if "/crossmatch/" in path:
                return "blood_bank.crossmatch"

            return "blood_bank.view"

        if path.startswith("/blood_bank/issues/") and "/start-transfusion/" in path:
            return "blood_bank.transfusion"

        if path.startswith("/blood_bank/transfusions/"):
            return "blood_bank.transfusion"

        if path.startswith("/blood_bank/movements/"):
            return "blood_bank.receive"

        if path.startswith("/blood_bank/patients/"):
            return "blood_bank.view"

        if path.startswith("/blood_bank/"):
            return "blood_bank.view"

        # ============================================================
        # Billing
        # ============================================================
        if path.startswith("/billing/bills/create/"):
            return "billing.create"

        if path.startswith("/billing/bills/"):
            if "/items/create/" in path:
                return "billing.items.create"

            if "/payments/create/" in path:
                return "billing.payment"

            if "/status/" in path:
                return "billing.status"

            if "/edit/" in path:
                return "billing.edit"

            return "billing.view"

        if path.startswith("/billing/items/") and "/delete/" in path:
            return "billing.items.delete"

        if path.startswith("/billing/patients/"):
            return "billing.view"

        if path.startswith("/billing/"):
            return "billing.view"

        return None

