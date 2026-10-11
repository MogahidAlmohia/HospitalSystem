from django.core.management.base import BaseCommand
from departments.models import Department


DEPARTMENTS = [
    # =========================
    # الأقسام السريرية
    # =========================
    ("ER", "الطوارئ", "Emergency", "CLINICAL"),
    ("IM", "الباطنية", "Internal Medicine", "CLINICAL"),
    ("SURG", "الجراحة العامة", "General Surgery", "CLINICAL"),
    ("PED", "طب الأطفال", "Pediatrics", "CLINICAL"),
    ("OBGYN", "النساء والولادة", "Obstetrics & Gynecology", "CLINICAL"),
    ("CARD", "أمراض القلب", "Cardiology", "CLINICAL"),
    ("ICU", "العناية المركزة", "Intensive Care Unit", "CLINICAL"),
    ("NEPH", "أمراض الكلى والغسيل", "Nephrology & Dialysis", "CLINICAL"),
    ("URO", "المسالك البولية", "Urology", "CLINICAL"),
    ("ORTHO", "العظام", "Orthopedics", "CLINICAL"),
    ("NEURO", "الأعصاب", "Neurology", "CLINICAL"),
    ("ENT", "الأنف والأذن والحنجرة", "ENT", "CLINICAL"),
    ("OPH", "العيون", "Ophthalmology", "CLINICAL"),
    ("DERM", "الجلدية", "Dermatology", "CLINICAL"),
    ("ONCO", "الأورام", "Oncology", "CLINICAL"),
    ("INF", "الأمراض المعدية", "Infectious Diseases", "CLINICAL"),
    ("ENDO", "الغدد الصماء", "Endocrinology", "CLINICAL"),
    ("GASTRO", "الجهاز الهضمي", "Gastroenterology", "CLINICAL"),
    ("PULM", "أمراض الصدر والجهاز التنفسي", "Pulmonology", "CLINICAL"),
    ("RHEUM", "الروماتيزم", "Rheumatology", "CLINICAL"),
    ("DENT", "طب الأسنان", "Dentistry", "CLINICAL"),
    ("PSY", "الطب النفسي", "Psychiatry", "CLINICAL"),
    ("BURNS", "الحروق", "Burns Unit", "CLINICAL"),
    ("NICU", "العناية المركزة لحديثي الولادة", "NICU", "CLINICAL"),
    ("PICU", "العناية المركزة للأطفال", "PICU", "CLINICAL"),

    # =========================
    # أقسام التشخيص والمختبر
    # =========================
    ("LAB", "المختبر المركزي", "Central Laboratory", "DIAGNOSTIC"),
    ("HEM", "أمراض الدم", "Hematology", "DIAGNOSTIC"),
    ("CHEM", "الكيمياء السريرية", "Clinical Chemistry", "DIAGNOSTIC"),
    ("IMM", "المناعة والأمصال", "Serology & Immunology", "DIAGNOSTIC"),
    ("MICRO", "الأحياء الدقيقة", "Microbiology", "DIAGNOSTIC"),
    ("BACT", "البكتيريا", "Bacteriology", "DIAGNOSTIC"),
    ("PARA", "الطفيليات", "Parasitology", "DIAGNOSTIC"),
    ("UA", "تحليل البول", "Urinalysis", "DIAGNOSTIC"),
    ("COAG", "التخثر", "Coagulation", "DIAGNOSTIC"),
    ("BB", "بنك الدم", "Blood Bank", "DIAGNOSTIC"),
    ("HORM", "الهرمونات", "Hormones", "DIAGNOSTIC"),
    ("TM", "الواسمات الورمية", "Tumor Markers", "DIAGNOSTIC"),
    ("VIR", "الفيروسات", "Virology", "DIAGNOSTIC"),
    ("MOLEC", "الأحياء الجزيئية", "Molecular Diagnostics", "DIAGNOSTIC"),
    ("MYCO", "الفطريات", "Mycology", "DIAGNOSTIC"),
    ("RAD", "الأشعة", "Radiology", "DIAGNOSTIC"),

    # =========================
    # الأقسام التشغيلية والخدمات
    # =========================
    ("PHARM", "الصيدلية", "Pharmacy", "SUPPORT"),
    ("RECEPTION", "الاستقبال", "Reception", "ADMIN"),
    ("INPATIENT", "التنويم", "Inpatient Department", "CLINICAL"),
    ("OR", "غرف العمليات", "Operating Room", "CLINICAL"),
    ("NURSING", "التمريض", "Nursing", "CLINICAL"),
    ("ACCOUNT", "الحسابات", "Accounting", "ADMIN"),
    ("INVENTORY", "المخازن والمستودعات", "Inventory", "SUPPORT"),
    ("HR", "الموارد البشرية", "Human Resources", "ADMIN"),
    ("ADMIN", "الإدارة", "Administration", "ADMIN"),
    ("USERS", "المستخدمون والصلاحيات", "Users & Permissions", "ADMIN"),
]


class Command(BaseCommand):
    help = "Create or update hospital and laboratory departments"

    def handle(self, *args, **options):
        created = 0
        updated = 0

        for code, name_ar, name_en, department_type in DEPARTMENTS:
            department, was_created = Department.objects.update_or_create(
                code=code,
                defaults={
                    "name_ar": name_ar,
                    "name_en": name_en,
                    "department_type": department_type,
                    "is_active": True,
                },
            )

            if was_created:
                created += 1
            else:
                updated += 1

        total = Department.objects.filter(is_active=True).count()

        self.stdout.write(
            self.style.SUCCESS(
                f"تم إنشاء {created} قسم وتحديث {updated} قسم. "
                f"إجمالي الأقسام النشطة: {total}"
            )
        )
