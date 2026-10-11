from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render
from django.utils import timezone

from patients.models import Patient, Visit
from laboratory.models import LaboratoryOrder, LaboratoryOrderItem
from departments.models import Department


@login_required
def reports_dashboard(request):
    """
    مركز التقارير العام HIS / LIS.

    هذه الصفحة لا تنشئ بيانات جديدة ولا تعدّل قاعدة البيانات.
    تعتمد فقط على البيانات الموجودة في النظام.
    """

    today = timezone.localdate()

    # --------------------------------------------------------
    # صلاحية الإدارة العامة للتقارير
    # --------------------------------------------------------
    is_admin = request.user.is_superuser

    try:
        profile = request.user.staff_profile
        is_admin = is_admin or (
            profile.is_active
            and profile.role in ["ADMIN", "MANAGER"]
        )
    except Exception:
        pass

    # --------------------------------------------------------
    # الأقسام المتاحة للمستخدم
    # --------------------------------------------------------
    departments = Department.objects.filter(
        is_active=True
    ).order_by("name_ar")

    # --------------------------------------------------------
    # المرضى
    # --------------------------------------------------------
    total_patients = Patient.objects.count()

    today_patients = Patient.objects.filter(
        created_at__date=today
    ).count()

    # --------------------------------------------------------
    # الزيارات
    # --------------------------------------------------------
    total_visits = Visit.objects.count()

    today_visits = Visit.objects.filter(
        created_at__date=today
    ).count()

    # --------------------------------------------------------
    # المختبر
    # --------------------------------------------------------
    total_lab_orders = LaboratoryOrder.objects.count()

    today_lab_orders = LaboratoryOrder.objects.filter(
        requested_at__date=today
    ).count()

    completed_lab_orders = LaboratoryOrder.objects.filter(
        status="COMPLETED"
    ).count()

    pending_lab_orders = LaboratoryOrder.objects.filter(
        status__in=[
            "REQUESTED",
            "RECEIVED",
            "COLLECTED",
            "PROCESSING",
        ]
    ).count()

    critical_results = LaboratoryOrderItem.objects.filter(
        critical_status__in=[
            "CRITICAL_LOW",
            "CRITICAL_HIGH",
        ],
        verified=False,
    ).count()

    # --------------------------------------------------------
    # الأقسام — إحصائيات مختصرة
    # --------------------------------------------------------
    department_stats = []

    for department in departments:
        patient_count = Patient.objects.filter(
            visits__department=department
        ).distinct().count()

        visit_count = Visit.objects.filter(
            department=department
        ).count()

        lab_count = LaboratoryOrder.objects.filter(
            requesting_department=department
        ).count()

        today_visit_count = Visit.objects.filter(
            department=department,
            created_at__date=today,
        ).count()

        department_stats.append({
            "department": department,
            "patient_count": patient_count,
            "visit_count": visit_count,
            "lab_count": lab_count,
            "today_visit_count": today_visit_count,
        })

    context = {
        "today": today,
        "is_admin": is_admin,

        "total_patients": total_patients,
        "today_patients": today_patients,

        "total_visits": total_visits,
        "today_visits": today_visits,

        "total_lab_orders": total_lab_orders,
        "today_lab_orders": today_lab_orders,
        "completed_lab_orders": completed_lab_orders,
        "pending_lab_orders": pending_lab_orders,
        "critical_results": critical_results,

        "department_stats": department_stats,
    }

    return render(
        request,
        "reports/dashboard.html",
        context,
    )

@login_required
def patient_file_pdf(request, patient_id):
    """
    ملف المريض السريري PDF — HIS / LIS.
    يعرض البيانات الأساسية + الزيارات + التشخيصات.
    """
    from pathlib import Path
    import re
    from io import BytesIO

    from django.http import HttpResponse
    from django.shortcuts import get_object_or_404

    from patients.models import ClinicalDiagnosis, Patient, Visit
    from accounts.permissions import user_has_permission
    from system_settings.services import get_hospital_identity

    if not user_has_permission(request.user, "patients.view"):
        return redirect("/")

    patient = get_object_or_404(
        Patient.objects.prefetch_related(
            "visits__department",
            "visits__doctor",
            "clinical_diagnoses__department",
            "clinical_diagnoses__doctor",
        ),
        pk=patient_id,
    )

    visits = list(
        patient.visits.all().order_by("-created_at")
    )

    diagnoses = list(
        ClinicalDiagnosis.objects.filter(
            patient=patient
        ).select_related(
            "department",
            "doctor",
            "visit",
        ).order_by("-created_at")
    )

    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        KeepTogether,
    )

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
    # Hospital identity
    # ---------------------------------------------------------
    hospital = get_hospital_identity(
        {
            "name_ar": "نظام إدارة المستشفى",
            "name_en": "Hospital HIS / LIS",
            "address": "",
            "phone": "",
            "email": "",
        }
    )

    # ---------------------------------------------------------
    # Fonts
    # ---------------------------------------------------------
    font_dir = (
        Path(__file__).resolve().parent.parent
        / "laboratory"
        / "fonts"
    )

    regular_path = font_dir / "NotoNaskhArabic-Regular.ttf"
    bold_path = font_dir / "NotoNaskhArabic-Bold.ttf"

    AR_FONT = "Helvetica"
    AR_BOLD = "Helvetica-Bold"

    if regular_path.exists():
        try:
            pdfmetrics.registerFont(
                TTFont("PatientNotoArabic", str(regular_path))
            )
            AR_FONT = "PatientNotoArabic"

            if bold_path.exists():
                pdfmetrics.registerFont(
                    TTFont("PatientNotoArabicBold", str(bold_path))
                )
                AR_BOLD = "PatientNotoArabicBold"

        except Exception:
            pass

    # ---------------------------------------------------------
    # PDF
    # ---------------------------------------------------------
    buffer = BytesIO()

    response = HttpResponse(
        content_type="application/pdf"
    )

    safe_number = re.sub(
        r"[^A-Za-z0-9_-]",
        "_",
        str(patient.patient_number),
    )

    response["Content-Disposition"] = (
        f'inline; filename="patient_file_{safe_number}.pdf"'
    )

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=14 * mm,
        bottomMargin=16 * mm,
        title=f"Patient File - {patient.patient_number}",
        author="Hospital HIS / LIS",
    )

    title_style = ParagraphStyle(
        "PatientTitle",
        fontName=AR_BOLD,
        fontSize=18,
        leading=24,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#123b63"),
        spaceAfter=4 * mm,
    )

    subtitle_style = ParagraphStyle(
        "PatientSubtitle",
        fontName=AR_FONT,
        fontSize=9,
        leading=13,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#667788"),
        spaceAfter=5 * mm,
    )

    section_style = ParagraphStyle(
        "Section",
        fontName=AR_BOLD,
        fontSize=12,
        leading=17,
        alignment=TA_RIGHT,
        textColor=colors.white,
    )

    normal_style = ParagraphStyle(
        "NormalArabic",
        fontName=AR_FONT,
        fontSize=9.5,
        leading=14,
        alignment=TA_RIGHT,
    )

    small_style = ParagraphStyle(
        "SmallArabic",
        fontName=AR_FONT,
        fontSize=8,
        leading=12,
        alignment=TA_RIGHT,
    )

    story = []

    # ---------------------------------------------------------
    # Header
    # ---------------------------------------------------------
    hospital_name = hospital.get("name_ar") or hospital.get("name_en") or "HIS / LIS"

    story.append(
        Paragraph(
            ar(hospital_name),
            title_style,
        )
    )

    identity_parts = [
        hospital.get("address"),
        hospital.get("phone"),
        hospital.get("email"),
    ]
    identity_line = " | ".join(
        str(x).strip()
        for x in identity_parts
        if str(x or "").strip()
    )

    if identity_line:
        story.append(
            Paragraph(
                ar(identity_line),
                subtitle_style,
            )
        )

    story.append(
        Paragraph(
            ar("ملف المريض السريري"),
            title_style,
        )
    )

    story.append(
        Paragraph(
            ar(f"رقم الملف: {patient.patient_number}"),
            subtitle_style,
        )
    )

    # ---------------------------------------------------------
    # Patient information
    # ---------------------------------------------------------
    story.append(
        Table(
            [
                [
                    Paragraph(ar("اسم المريض"), section_style),
                    Paragraph(ar(patient.full_name), normal_style),
                    Paragraph(ar("رقم الملف"), section_style),
                    Paragraph(ar(patient.patient_number), normal_style),
                ],
                [
                    Paragraph(ar("الجنس"), section_style),
                    Paragraph(ar(patient.get_gender_display()), normal_style),
                    Paragraph(ar("العمر"), section_style),
                    Paragraph(ar(patient.age or ""), normal_style),
                ],
                [
                    Paragraph(ar("تاريخ الميلاد"), section_style),
                    Paragraph(ar(patient.date_of_birth or ""), normal_style),
                    Paragraph(ar("فصيلة الدم"), section_style),
                    Paragraph(ar(patient.blood_group or ""), normal_style),
                ],
                [
                    Paragraph(ar("الهاتف"), section_style),
                    Paragraph(ar(patient.phone or ""), normal_style),
                    Paragraph(ar("رقم الهوية"), section_style),
                    Paragraph(ar(patient.national_id or ""), normal_style),
                ],
                [
                    Paragraph(ar("العنوان"), section_style),
                    Paragraph(ar(patient.address or ""), normal_style),
                    Paragraph(ar("جهة اتصال الطوارئ"), section_style),
                    Paragraph(
                        ar(
                            f"{patient.emergency_contact_name or ''} "
                            f"{patient.emergency_contact_phone or ''}"
                        ),
                        normal_style,
                    ),
                ],
            ],
            colWidths=[27 * mm, 63 * mm, 27 * mm, 63 * mm],
            repeatRows=0,
            hAlign="RIGHT",
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#0d6efd")),
                    ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#0d6efd")),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors.white),
                    ("TEXTCOLOR", (2, 0), (2, -1), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d7e0ea")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            ),
        )
    )

    story.append(Spacer(1, 5 * mm))

    # ---------------------------------------------------------
    # Alerts / medical notes
    # ---------------------------------------------------------
    story.append(
        Table(
            [
                [
                    Paragraph(ar("الحساسيات"), section_style),
                    Paragraph(ar(patient.allergies or "لا توجد بيانات مسجلة"), normal_style),
                ],
                [
                    Paragraph(ar("الملاحظات الطبية"), section_style),
                    Paragraph(ar(patient.medical_notes or "لا توجد ملاحظات مسجلة"), normal_style),
                ],
            ],
            colWidths=[35 * mm, 145 * mm],
            hAlign="RIGHT",
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#dc3545")),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d7e0ea")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            ),
        )
    )

    story.append(Spacer(1, 5 * mm))

    # ---------------------------------------------------------
    # Diagnoses
    # ---------------------------------------------------------
    story.append(
        Table(
            [[Paragraph(ar("التشخيصات والأمراض"), section_style)]],
            colWidths=[180 * mm],
            hAlign="RIGHT",
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#198754")),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            ),
        )
    )

    diagnosis_rows = [
        [
            Paragraph(ar("التشخيص"), section_style),
            Paragraph(ar("القسم"), section_style),
            Paragraph(ar("الطبيب"), section_style),
            Paragraph(ar("ICD-10"), section_style),
            Paragraph(ar("الحالة"), section_style),
        ]
    ]

    for diagnosis in diagnoses:
        diagnosis_rows.append(
            [
                Paragraph(ar(diagnosis.diagnosis_name), normal_style),
                Paragraph(ar(diagnosis.department.name_ar if diagnosis.department else ""), small_style),
                Paragraph(ar(str(diagnosis.doctor) if diagnosis.doctor else ""), small_style),
                Paragraph(ar(diagnosis.icd10_code or ""), small_style),
                Paragraph(ar(diagnosis.get_status_display()), small_style),
            ]
        )

    if len(diagnosis_rows) == 1:
        diagnosis_rows.append(
            [
                Paragraph(ar("لا توجد تشخيصات مسجلة"), normal_style),
                "",
                "",
                "",
                "",
            ]
        )

    story.append(
        Table(
            diagnosis_rows,
            colWidths=[58 * mm, 30 * mm, 35 * mm, 25 * mm, 32 * mm],
            repeatRows=1,
            hAlign="RIGHT",
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#198754")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d7e0ea")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            ),
        )
    )

    story.append(Spacer(1, 5 * mm))

    # ---------------------------------------------------------
    # Visits
    # ---------------------------------------------------------
    story.append(
        Table(
            [[Paragraph(ar("سجل الزيارات"), section_style)]],
            colWidths=[180 * mm],
            hAlign="RIGHT",
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0d6efd")),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            ),
        )
    )

    visit_rows = [
        [
            Paragraph(ar("رقم الزيارة"), section_style),
            Paragraph(ar("القسم"), section_style),
            Paragraph(ar("الطبيب"), section_style),
            Paragraph(ar("النوع"), section_style),
            Paragraph(ar("الحالة"), section_style),
            Paragraph(ar("التاريخ"), section_style),
        ]
    ]

    for visit in visits:
        visit_rows.append(
            [
                Paragraph(ar(visit.visit_number), small_style),
                Paragraph(ar(visit.department.name_ar if visit.department else ""), small_style),
                Paragraph(ar(str(visit.doctor) if visit.doctor else ""), small_style),
                Paragraph(ar(visit.get_visit_type_display()), small_style),
                Paragraph(ar(visit.get_status_display()), small_style),
                Paragraph(ar(visit.created_at.strftime("%Y-%m-%d %H:%M") if visit.created_at else ""), small_style),
            ]
        )

    if len(visit_rows) == 1:
        visit_rows.append(
            [
                Paragraph(ar("لا توجد زيارات مسجلة"), normal_style),
                "",
                "",
                "",
                "",
                "",
            ]
        )

    story.append(
        Table(
            visit_rows,
            colWidths=[31 * mm, 34 * mm, 36 * mm, 25 * mm, 25 * mm, 29 * mm],
            repeatRows=1,
            hAlign="RIGHT",
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d6efd")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d7e0ea")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            ),
        )
    )

    story.append(Spacer(1, 5 * mm))

    # ---------------------------------------------------------
    # Footer
    # ---------------------------------------------------------
    story.append(
        Paragraph(
            ar("تم إنشاء هذا الملف بواسطة نظام إدارة المستشفى HIS / LIS"),
            subtitle_style,
        )
    )

    doc.build(story)

    pdf = buffer.getvalue()
    buffer.close()

    response.write(pdf)
    return response
