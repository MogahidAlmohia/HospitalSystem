from django.db import models
from patients.models import Patient, Visit
from departments.models import Department
from doctors.models import Doctor


class LaboratoryTest(models.Model):

    SAMPLE_TYPES = [
        ("SERUM", "Serum"),
        ("PLASMA", "Plasma"),
        ("WHOLE_BLOOD", "Whole Blood"),
        ("URINE", "Urine"),
        ("STOOL", "Stool"),
        ("CSF", "CSF"),
        ("SWAB", "Swab"),
        ("SEMEN", "Semen"),
        ("BONE_MARROW", "Bone Marrow"),
        ("OTHER", "Other"),
    ]

    code = models.CharField(
        max_length=50,
        unique=True
    )

    name_en = models.CharField(
        max_length=200
    )

    name_ar = models.CharField(

        max_length=200,

        blank=True,

        default="",

    )


    short_name_en = models.CharField(

        max_length=100,

        blank=True,

        default="",

        verbose_name="Short Name English",

    )


    short_name_ar = models.CharField(

        max_length=100,

        blank=True,

        default="",

        verbose_name="الاسم المختصر بالعربي",

    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="laboratory_tests"
    )

    sample_type = models.CharField(
        max_length=30,
        choices=SAMPLE_TYPES,
        default="SERUM"
    )

    unit = models.CharField(
        max_length=100,
        blank=True
    )

    device = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Device"
    )

    reagent = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Reagent"
    )

    reference_range = models.CharField(
        max_length=200,
        blank=True
    )

    critical_low = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name="Critical Low"
    )

    critical_high = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name="Critical High"
    )

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # -------------------------------------------------
    # Report table column widths
    # -------------------------------------------------

    auto_column_widths = models.BooleanField(
        default=True,
        verbose_name="ضبط أعمدة الجدول تلقائياً",
    )

    column_width_number = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=10,
        verbose_name="عرض عمود الرقم mm",
    )

    column_width_test = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=34,
        verbose_name="عرض عمود اسم التحليل mm",
    )

    column_width_test_code = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=20,
        verbose_name="عرض عمود Code mm",
    )

    column_width_result = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=25,
        verbose_name="عرض عمود النتيجة mm",
    )

    column_width_unit = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=18,
        verbose_name="عرض عمود الوحدة mm",
    )

    column_width_reference = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=35,
        verbose_name="عرض عمود Reference Range mm",
    )

    column_width_flag = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=14,
        verbose_name="عرض عمود Flag mm",
    )

    column_width_critical = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=18,
        verbose_name="عرض عمود Critical mm",
    )

    column_width_sample = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=22,
        verbose_name="عرض عمود Sample mm",
    )

    column_width_device = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=25,
        verbose_name="عرض عمود Device mm",
    )

    column_width_reagent = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=25,
        verbose_name="عرض عمود Reagent mm",
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.code} - {self.name_en}"

    class Meta:
        ordering = ["department__name_en", "name_en"]


class LaboratoryOrder(models.Model):

    STATUS_CHOICES = [
        ("REQUESTED", "Requested"),
        ("RECEIVED", "Received"),
        ("COLLECTED", "Sample Collected"),
        ("PROCESSING", "Processing"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]

    PRIORITY_CHOICES = [
        ("NORMAL", "Normal"),
        ("URGENT", "Urgent"),
        ("STAT", "STAT"),
    ]

    order_number = models.CharField(
        max_length=50,
        unique=True
    )

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="laboratory_orders"
    )

    visit = models.ForeignKey(
        Visit,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="laboratory_orders"
    )

    admission = models.ForeignKey(
        "inpatient.Admission",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="laboratory_orders",
        verbose_name="Inpatient Admission",
    )

    requesting_department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="laboratory_orders"
    )

    requesting_doctor = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="laboratory_orders"
    )

    clinical_notes = models.TextField(
        blank=True
    )

    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default="NORMAL"
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="REQUESTED"
    )

    requested_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.order_number} - {self.patient.full_name}"

    class Meta:
        ordering = ["-requested_at"]


class LaboratoryOrderItem(models.Model):

    STATUS_CHOICES = [
        ("REQUESTED", "Requested"),
        ("RECEIVED", "Received"),
        ("COLLECTED", "Collected"),
        ("PROCESSING", "Processing"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
        ("REJECTED", "Rejected"),
    ]

    order = models.ForeignKey(
        LaboratoryOrder,
        on_delete=models.CASCADE,
        related_name="items"
    )

    test = models.ForeignKey(
        LaboratoryTest,
        on_delete=models.PROTECT,
        related_name="order_items"
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="REQUESTED"
    )

    sample_id = models.CharField(
        max_length=100,
        blank=True
    )

    sample_collected_at = models.DateTimeField(
        null=True,
        blank=True
    )

    rejection_reason = models.TextField(
        blank=True
    )

    rejected_at = models.DateTimeField(
        null=True,
        blank=True
    )

    rejected_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="laboratory_rejected_samples"
    )

    resample_count = models.PositiveIntegerField(
        default=0
    )

    result = models.TextField(
        blank=True
    )

    result_numeric = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        null=True,
        blank=True
    )

    result_flag = models.CharField(
        max_length=20,
        blank=True
    )

    critical_status = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ("CRITICAL_LOW", "Critical Low"),
            ("CRITICAL_HIGH", "Critical High"),
        ]
    )

    critical_detected_at = models.DateTimeField(
        null=True,
        blank=True
    )

    examiner_notes = models.TextField(
        blank=True
    )

    examiner = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="laboratory_examined_results"
    )

    examined_at = models.DateTimeField(
        null=True,
        blank=True
    )

    verified = models.BooleanField(
        default=False
    )

    verified_at = models.DateTimeField(
        null=True,
        blank=True
    )

    verified_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="laboratory_verified_results"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.order.order_number} - {self.test.name_en}"

    class Meta:
        ordering = ["id"]

# ============================================================
# Laboratory Report Settings
# ============================================================


class LaboratoryResultDelivery(models.Model):
    """
    سجل إرسال نتيجة المختبر إلى القسم أو الطبيب.
    لا يحذف أو يغير نتيجة المختبر الأصلية.
    """

    order = models.ForeignKey(
        LaboratoryOrder,
        on_delete=models.CASCADE,
        related_name="result_deliveries",
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="laboratory_result_deliveries",
    )

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="laboratory_result_deliveries",
    )

    sent_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="laboratory_result_deliveries",
    )

    sent_at = models.DateTimeField(auto_now_add=True)

    received = models.BooleanField(
        default=False,
        verbose_name="Received",
    )

    received_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Received At",
    )

    received_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="laboratory_result_receipts",
        verbose_name="Received By",
    )

    note = models.TextField(
        blank=True,
        verbose_name="Delivery Note",
    )

    class Meta:
        ordering = ["-sent_at"]
        verbose_name = "Laboratory Result Delivery"
        verbose_name_plural = "Laboratory Result Deliveries"

    def __str__(self):
        destination = []

        if self.department:
            destination.append(
                f"Department: {self.department.name_ar} - {self.department.name_en}"
            )

        if self.doctor:
            destination.append(
                f"Doctor: {self.doctor.full_name}"
            )

        destination_text = " / ".join(destination) or "No destination"

        return f"{self.order.order_number} - {destination_text}"
        


class LaboratoryAuditLog(models.Model):
    """
    سجل تدقيق عمليات المختبر.
    لا يحذف أو يعدل البيانات الأصلية للطلبات أو النتائج.
    """

    ACTION_CHOICES = [
        ("CREATE_ORDER", "Create Order"),
        ("ENTER_RESULT", "Enter Result"),
        ("VERIFY_RESULT", "Verify Result"),
        ("SEND_RESULT", "Send Result"),
        ("RECEIVE_RESULT", "Receive Result"),
        ("UPDATE_RESULT", "Update Result"),
        ("CANCEL_ORDER", "Cancel Order"),
        ("OTHER", "Other"),
    ]

    order = models.ForeignKey(
        LaboratoryOrder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        verbose_name="Laboratory Order",
    )

    user = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="laboratory_audit_logs",
        verbose_name="User",
    )

    action = models.CharField(
        max_length=30,
        choices=ACTION_CHOICES,
        verbose_name="Action",
    )

    description = models.TextField(
        blank=True,
        verbose_name="Description",
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="IP Address",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Laboratory Audit Log"
        verbose_name_plural = "Laboratory Audit Logs"

    def __str__(self):
        order_number = (
            self.order.order_number
            if self.order
            else "No Order"
        )

        username = (
            self.user.username
            if self.user
            else "System"
        )

        return (
            f"{order_number} - "
            f"{self.get_action_display()} - "
            f"{username}"
        )


class LaboratoryReportSettings(models.Model):

    # =================================================
    # Report language
    # =================================================

    report_language = models.CharField(
        max_length=20,
        choices=[
            ("AR", "العربية"),
            ("EN", "English"),
            ("BOTH", "العربية + English"),
        ],
        default="BOTH",
        verbose_name="لغة التقرير",
    )

    test_name_language = models.CharField(
        max_length=20,
        choices=[
            ("AR", "العربية"),
            ("EN", "English"),
            ("BOTH", "العربية + English"),
        ],
        default="EN",
        verbose_name="لغة أسماء التحاليل",
    )

    test_name_display = models.CharField(
        max_length=20,
        choices=[
            ("FULL", "الاسم الكامل"),
            ("SHORT", "الاسم المختصر"),
            ("FULL_SHORT", "الكامل + المختصر"),
        ],
        default="FULL",
        verbose_name="طريقة عرض اسم التحليل",
    )

    # =================================================
    # Report table columns
    # =================================================

    auto_column_widths = models.BooleanField(
        default=True,
        verbose_name="ضبط أعمدة التقرير تلقائياً",
    )

    column_width_number = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=10,
        verbose_name="عرض رقم التحليل mm",
    )

    column_width_test = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=34,
        verbose_name="عرض اسم التحليل mm",
    )

    column_width_test_code = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=20,
        verbose_name="عرض Code mm",
    )

    column_width_result = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=25,
        verbose_name="عرض النتيجة mm",
    )

    column_width_unit = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=18,
        verbose_name="عرض الوحدة mm",
    )

    column_width_reference = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=35,
        verbose_name="عرض Reference Range mm",
    )

    column_width_flag = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=14,
        verbose_name="عرض Flag mm",
    )

    column_width_critical = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=18,
        verbose_name="عرض Critical mm",
    )

    column_width_sample = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=22,
        verbose_name="عرض Sample mm",
    )

    column_width_device = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=25,
        verbose_name="عرض Device mm",
    )

    column_width_reagent = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=25,
        verbose_name="عرض Reagent mm",
    )


    # =========================================================
    # بيانات المنشأة
    # =========================================================

    hospital_name_ar = models.CharField(
        max_length=200,
        default="اسم المستشفى"
    )

    hospital_name_en = models.CharField(
        max_length=200,
        default="Hospital Name"
    )

    laboratory_name_ar = models.CharField(
        max_length=200,
        default="قسم المختبرات الطبية"
    )

    laboratory_name_en = models.CharField(
        max_length=200,
        default="Medical Laboratory Department"
    )

    address = models.CharField(
        max_length=300,
        blank=True
    )

    phone = models.CharField(
        max_length=100,
        blank=True
    )

    email = models.EmailField(
        blank=True
    )

    logo = models.ImageField(
        upload_to="laboratory/logos/",
        blank=True,
        null=True
    )

    # =========================================================
    # عنوان التقرير
    # =========================================================

    report_title_ar = models.CharField(
        max_length=200,
        default="تقرير نتائج الفحوصات المخبرية"
    )

    report_title_en = models.CharField(
        max_length=200,
        default="Laboratory Report"
    )

    report_subtitle_ar = models.CharField(
        max_length=300,
        blank=True,
        default=""
    )

    report_subtitle_en = models.CharField(
        max_length=300,
        blank=True,
        default=""
    )

    # =========================================================
    # بيانات التقرير
    # =========================================================

    show_report_number = models.BooleanField(default=True)
    show_report_date = models.BooleanField(default=True)
    show_report_time = models.BooleanField(default=True)
    show_generated_datetime = models.BooleanField(default=True)

    # =========================================================
    # بيانات المريض
    # =========================================================

    show_patient_number = models.BooleanField(default=True)
    show_patient_name = models.BooleanField(default=True)
    show_patient_age = models.BooleanField(default=True)
    show_patient_gender = models.BooleanField(default=True)
    show_patient_phone = models.BooleanField(default=True)
    show_patient_address = models.BooleanField(default=False)
    show_visit_number = models.BooleanField(default=True)
    show_requesting_department = models.BooleanField(default=True)
    show_requesting_doctor = models.BooleanField(default=True)

    # =========================================================
    # نتائج المختبر
    # =========================================================

    show_test_code = models.BooleanField(default=True)
    show_test_name = models.BooleanField(default=True)
    show_result = models.BooleanField(default=True)
    show_unit = models.BooleanField(default=True)
    show_reference_range = models.BooleanField(default=True)
    show_result_flag = models.BooleanField(default=True)
    show_critical_status = models.BooleanField(default=True)

    show_sample_type = models.BooleanField(default=False)
    show_device = models.BooleanField(default=False)
    show_reagent = models.BooleanField(default=False)

    # =========================================================
    # الملاحظات
    # =========================================================

    show_examiner_notes = models.BooleanField(default=True)

    # =========================================================
    # التوقيعات والاعتماد
    # =========================================================

    show_examiner_signature = models.BooleanField(default=True)
    show_verifier_signature = models.BooleanField(default=True)
    show_director_signature = models.BooleanField(default=True)

    examiner_signature_label = models.CharField(
        max_length=150,
        default="Examiner / فني المختبر"
    )

    verifier_signature_label = models.CharField(
        max_length=150,
        default="Verified By / اعتماد النتيجة"
    )

    director_signature_label = models.CharField(
        max_length=150,
        default="Laboratory Director / مدير المختبر"
    )

    # =========================================================
    # التذييل
    # =========================================================

    show_footer = models.BooleanField(default=True)

    report_footer = models.TextField(
        blank=True,
        default="نتيجة الفحص للاستخدام الطبي فقط."
    )

    report_footer_en = models.TextField(
        blank=True,
        default="This report is for medical use only."
    )

    # =========================================================
    # التصميم
    # =========================================================

    accent_color = models.CharField(
        max_length=20,
        default="#0d6efd"
    )

    table_header_color = models.CharField(
        max_length=20,
        default="#0d6efd"
    )

    table_header_text_color = models.CharField(
        max_length=20,
        default="#ffffff"
    )

    report_background_color = models.CharField(
        max_length=20,
        default="#ffffff"
    )

    show_logo = models.BooleanField(default=True)

    logo_position = models.CharField(
        max_length=20,
        choices=[
            ("LEFT", "Left"),
            ("CENTER", "Center"),
            ("RIGHT", "Right"),
        ],
        default="CENTER"
    )

    # =========================================================
    # العلامة المائية
    # =========================================================

    watermark_enabled = models.BooleanField(default=False)

    watermark_text = models.CharField(
        max_length=200,
        default="LABORATORY"
    )

    watermark_opacity = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=0.08
    )

    # =========================================================
    # الورق
    # =========================================================

    paper_size = models.CharField(
        max_length=20,
        choices=[
            ("A4", "A4"),
            ("A5", "A5"),
            ("LETTER", "Letter"),
        ],
        default="A4"
    )

    orientation = models.CharField(
        max_length=20,
        choices=[
            ("PORTRAIT", "Portrait"),
            ("LANDSCAPE", "Landscape"),
        ],
        default="PORTRAIT"
    )

    margin_top = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=14
    )

    margin_bottom = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=18
    )

    margin_left = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=12
    )

    margin_right = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=12
    )

    # =========================================================
    # الخطوط
    # =========================================================

    report_font_size = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=9.5
    )

    table_font_size = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=7.5
    )

    # =========================================================
    # الطباعة
    # =========================================================

    show_page_number = models.BooleanField(default=True)

    show_print_datetime = models.BooleanField(default=True)

    print_color = models.BooleanField(default=True)

    # =========================================================
    # الاتجاه
    # =========================================================

    rtl_layout = models.BooleanField(default=True)

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.hospital_name_ar

    class Meta:
        verbose_name = "Laboratory Report Settings"
        verbose_name_plural = "Laboratory Report Settings"
