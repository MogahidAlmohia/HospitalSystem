from django.db import models
from django.contrib.auth.models import User

from patients.models import Patient, Visit
from doctors.models import Doctor
from departments.models import Department


class BloodDonor(models.Model):
    BLOOD_GROUPS = [
        ("A+", "A+"),
        ("A-", "A-"),
        ("B+", "B+"),
        ("B-", "B-"),
        ("AB+", "AB+"),
        ("AB-", "AB-"),
        ("O+", "O+"),
        ("O-", "O-"),
    ]

    donor_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="رقم المتبرع",
    )
    full_name = models.CharField(
        max_length=200,
        verbose_name="اسم المتبرع",
    )
    national_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="رقم الهوية",
    )
    blood_group = models.CharField(
        max_length=5,
        choices=BLOOD_GROUPS,
        verbose_name="فصيلة الدم",
    )
    phone = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="الهاتف",
    )
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        verbose_name="تاريخ الميلاد",
    )
    address = models.TextField(
        blank=True,
        verbose_name="العنوان",
    )
    last_donation_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="آخر تاريخ تبرع",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="نشط",
    )
    notes = models.TextField(
        blank=True,
        verbose_name="ملاحظات",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["full_name"]
        verbose_name = "Blood Donor"
        verbose_name_plural = "Blood Donors"
        indexes = [
            models.Index(fields=["donor_number"]),
            models.Index(fields=["blood_group"]),
            models.Index(fields=["phone"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.donor_number} - {self.full_name}"


class BloodUnit(models.Model):
    COMPONENT_CHOICES = [
        ("WHOLE", "Whole Blood"),
        ("RBC", "Packed Red Blood Cells"),
        ("PLASMA", "Fresh Frozen Plasma"),
        ("PLATELETS", "Platelets"),
        ("CRYO", "Cryoprecipitate"),
    ]

    STATUS_CHOICES = [
        ("AVAILABLE", "Available"),
        ("RESERVED", "Reserved"),
        ("ISSUED", "Issued"),
        ("TRANSFUSED", "Transfused"),
        ("EXPIRED", "Expired"),
        ("DISCARDED", "Discarded"),
        ("QUARANTINE", "Quarantine"),
    ]

    unit_number = models.CharField(
        max_length=80,
        unique=True,
        verbose_name="رقم وحدة الدم",
    )
    donor = models.ForeignKey(
        BloodDonor,
        on_delete=models.PROTECT,
        related_name="blood_units",
        verbose_name="المتبرع",
    )
    blood_group = models.CharField(
        max_length=5,
        choices=BloodDonor.BLOOD_GROUPS,
        verbose_name="فصيلة الدم",
    )
    component = models.CharField(
        max_length=20,
        choices=COMPONENT_CHOICES,
        default="RBC",
        verbose_name="مكون الدم",
    )
    collection_date = models.DateField(
        verbose_name="تاريخ السحب",
    )
    expiry_date = models.DateField(
        verbose_name="تاريخ الانتهاء",
    )
    volume_ml = models.PositiveIntegerField(
        default=450,
        verbose_name="الحجم مل",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="AVAILABLE",
        verbose_name="الحالة",
    )
    storage_location = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="مكان التخزين",
    )
    screening_result = models.CharField(
        max_length=100,
        default="PENDING",
        verbose_name="نتيجة الفحص",
    )
    notes = models.TextField(
        blank=True,
        verbose_name="ملاحظات",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["expiry_date", "unit_number"]
        verbose_name = "Blood Unit"
        verbose_name_plural = "Blood Units"
        indexes = [
            models.Index(fields=["unit_number"]),
            models.Index(fields=["blood_group"]),
            models.Index(fields=["component"]),
            models.Index(fields=["status"]),
            models.Index(fields=["expiry_date"]),
        ]

    def __str__(self):
        return f"{self.unit_number} - {self.blood_group} - {self.component}"


class BloodRequest(models.Model):
    PRIORITY_CHOICES = [
        ("NORMAL", "Normal"),
        ("URGENT", "Urgent"),
        ("STAT", "STAT"),
    ]

    STATUS_CHOICES = [
        ("REQUESTED", "Requested"),
        ("CROSSMATCH", "Crossmatch"),
        ("READY", "Ready"),
        ("ISSUED", "Issued"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]

    request_number = models.CharField(
        max_length=60,
        unique=True,
        verbose_name="رقم طلب الدم",
    )
    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name="blood_requests",
        verbose_name="المريض",
    )
    visit = models.ForeignKey(
        Visit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="blood_requests",
        verbose_name="الزيارة",
    )
    requesting_doctor = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="blood_requests",
        verbose_name="الطبيب الطالب",
    )
    requesting_department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="blood_requests",
        verbose_name="القسم الطالب",
    )
    patient_blood_group = models.CharField(
        max_length=5,
        choices=BloodDonor.BLOOD_GROUPS,
        blank=True,
        verbose_name="فصيلة المريض",
    )
    component = models.CharField(
        max_length=20,
        choices=BloodUnit.COMPONENT_CHOICES,
        default="RBC",
        verbose_name="مكون الدم المطلوب",
    )
    units_requested = models.PositiveIntegerField(
        default=1,
        verbose_name="عدد الوحدات المطلوبة",
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default="NORMAL",
        verbose_name="الأولوية",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="REQUESTED",
        verbose_name="الحالة",
    )
    indication = models.TextField(
        blank=True,
        verbose_name="سبب طلب الدم",
    )
    notes = models.TextField(
        blank=True,
        verbose_name="ملاحظات",
    )
    requested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="blood_requests_created",
        verbose_name="تم الطلب بواسطة",
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="وقت الإكمال",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Blood Request"
        verbose_name_plural = "Blood Requests"
        indexes = [
            models.Index(fields=["request_number"]),
            models.Index(fields=["status"]),
            models.Index(fields=["priority"]),
            models.Index(fields=["patient"]),
            models.Index(fields=["created_at"]),
        ]

    def save(self, *args, **kwargs):
        if not self.request_number:
            from django.utils import timezone

            today = timezone.localdate().strftime("%Y%m%d")
            prefix = f"BLD-{today}-"

            last = (
                BloodRequest.objects
                .filter(request_number__startswith=prefix)
                .exclude(pk=self.pk)
                .order_by("-id")
                .first()
            )

            number = 1

            if last and last.request_number:
                try:
                    number = int(last.request_number.split("-")[-1]) + 1
                except (ValueError, IndexError):
                    number = 1

            self.request_number = f"{prefix}{number:04d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.request_number} - {self.patient.full_name}"


class BloodIssue(models.Model):
    request = models.ForeignKey(
        BloodRequest,
        on_delete=models.PROTECT,
        related_name="issues",
        verbose_name="طلب الدم",
    )
    blood_unit = models.ForeignKey(
        BloodUnit,
        on_delete=models.PROTECT,
        related_name="issues",
        verbose_name="وحدة الدم",
    )
    issued_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="blood_issues",
        verbose_name="تم الصرف بواسطة",
    )
    issued_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="وقت الصرف",
    )
    notes = models.TextField(
        blank=True,
        verbose_name="ملاحظات",
    )

    class Meta:
        ordering = ["-issued_at"]
        verbose_name = "Blood Issue"
        verbose_name_plural = "Blood Issues"
        constraints = [
            models.UniqueConstraint(
                fields=["request", "blood_unit"],
                name="unique_blood_issue_request_unit",
            )
        ]

    def __str__(self):
        return f"{self.request.request_number} - {self.blood_unit.unit_number}"


class BloodTransfusion(models.Model):
    STATUS_CHOICES = [
        ("STARTED", "Started"),
        ("COMPLETED", "Completed"),
        ("STOPPED", "Stopped"),
        ("REACTION", "Reaction"),
    ]

    issue = models.OneToOneField(
        BloodIssue,
        on_delete=models.PROTECT,
        related_name="transfusion",
        verbose_name="صرف الدم",
    )
    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name="blood_transfusions",
        verbose_name="المريض",
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="وقت البدء",
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="وقت الإكمال",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="STARTED",
        verbose_name="حالة نقل الدم",
    )
    reaction_notes = models.TextField(
        blank=True,
        verbose_name="ملاحظات التفاعل",
    )
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="blood_transfusions_performed",
        verbose_name="تم بواسطة",
    )
    notes = models.TextField(
        blank=True,
        verbose_name="ملاحظات",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Blood Transfusion"
        verbose_name_plural = "Blood Transfusions"
        indexes = [
            models.Index(fields=["patient"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.patient.full_name} - {self.issue.blood_unit.unit_number}"


class BloodBankMovement(models.Model):
    MOVEMENT_CHOICES = [
        ("COLLECTED", "Collected"),
        ("RECEIVED", "Received"),
        ("ISSUED", "Issued"),
        ("RETURNED", "Returned"),
        ("DISCARDED", "Discarded"),
        ("EXPIRED", "Expired"),
        ("ADJUSTMENT", "Adjustment"),
    ]

    blood_unit = models.ForeignKey(
        BloodUnit,
        on_delete=models.PROTECT,
        related_name="movements",
        verbose_name="وحدة الدم",
    )
    movement_type = models.CharField(
        max_length=20,
        choices=MOVEMENT_CHOICES,
        verbose_name="نوع الحركة",
    )
    from_location = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="من موقع",
    )
    to_location = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="إلى موقع",
    )
    reference = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="المرجع",
    )
    notes = models.TextField(
        blank=True,
        verbose_name="ملاحظات",
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="blood_bank_movements",
        verbose_name="بواسطة",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Blood Bank Movement"
        verbose_name_plural = "Blood Bank Movements"
        indexes = [
            models.Index(fields=["blood_unit"]),
            models.Index(fields=["movement_type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.blood_unit.unit_number} - {self.movement_type}"


class BloodCrossmatch(models.Model):
    """
    سجل اختبار توافق وحدة الدم مع طلب المريض قبل الصرف.
    """

    RESULT_CHOICES = [
        ("PENDING", "Pending"),
        ("COMPATIBLE", "Compatible"),
        ("INCOMPATIBLE", "Incompatible"),
        ("CANCELLED", "Cancelled"),
    ]

    request = models.ForeignKey(
        BloodRequest,
        on_delete=models.CASCADE,
        related_name="crossmatches",
    )

    blood_unit = models.ForeignKey(
        BloodUnit,
        on_delete=models.PROTECT,
        related_name="crossmatches",
    )

    patient_blood_group = models.CharField(
        max_length=5,
        choices=BloodDonor.BLOOD_GROUPS,
    )

    unit_blood_group = models.CharField(
        max_length=5,
        choices=BloodDonor.BLOOD_GROUPS,
    )

    result = models.CharField(
        max_length=20,
        choices=RESULT_CHOICES,
        default="PENDING",
    )

    tested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="blood_crossmatches",
    )

    tested_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    notes = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["request"]),
            models.Index(fields=["blood_unit"]),
            models.Index(fields=["result"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return (
            f"{self.request.request_number} - "
            f"{self.blood_unit.unit_number} - "
            f"{self.get_result_display()}"
        )
