from django.db import models
from django.contrib.auth.models import User
from patients.models import Patient, Visit
from doctors.models import Doctor


class SurgeryType(models.Model):
    name_ar = models.CharField(max_length=200, verbose_name="اسم العملية بالعربي")
    name_en = models.CharField(max_length=200, verbose_name="Surgery Name")
    code = models.CharField(max_length=50, unique=True, verbose_name="Surgery Code")
    specialty = models.CharField(max_length=100, blank=True)
    estimated_duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Estimated Duration (minutes)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name_ar"]

    def __str__(self):
        return f"{self.name_ar} - {self.name_en}"


class SurgeryOrder(models.Model):
    PRIORITY_CHOICES = [
        ("NORMAL", "Normal"),
        ("URGENT", "Urgent"),
        ("EMERGENCY", "Emergency"),
    ]

    STATUS_CHOICES = [
        ("REQUESTED", "Requested"),
        ("SCHEDULED", "Scheduled"),
        ("PREPARATION", "Preparation"),
        ("IN_PROGRESS", "In Progress"),
        ("RECOVERY", "Recovery"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]

    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name="surgery_orders"
    )
    visit = models.ForeignKey(
        Visit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="surgery_orders"
    )
    surgery_type = models.ForeignKey(
        SurgeryType,
        on_delete=models.PROTECT,
        related_name="orders"
    )
    surgeon = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="surgery_orders"
    )
    requested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="requested_surgeries"
    )

    order_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Surgery Order Number"
    )

    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default="NORMAL"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="REQUESTED"
    )

    diagnosis = models.TextField(blank=True)
    indication = models.TextField(blank=True)
    preoperative_notes = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    scheduled_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["patient"]),
            models.Index(fields=["visit"]),
            models.Index(fields=["surgery_type"]),
            models.Index(fields=["surgeon"]),
            models.Index(fields=["status"]),
            models.Index(fields=["priority"]),
            models.Index(fields=["created_at"]),
        ]

    def save(self, *args, **kwargs):
        if not self.order_number:
            from django.utils import timezone

            date_part = timezone.localdate().strftime("%Y%m%d")
            prefix = f"SUR-{date_part}-"

            last_order = (
                SurgeryOrder.objects
                .filter(order_number__startswith=prefix)
                .order_by("-order_number")
                .first()
            )

            if last_order:
                try:
                    last_number = int(last_order.order_number.split("-")[-1])
                except (ValueError, IndexError):
                    last_number = 0
            else:
                last_number = 0

            self.order_number = f"{prefix}{last_number + 1:04d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_number} - {self.patient.full_name}"


class SurgeryProcedure(models.Model):
    STATUS_CHOICES = [
        ("PLANNED", "Planned"),
        ("IN_PROGRESS", "In Progress"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]

    order = models.ForeignKey(
        SurgeryOrder,
        on_delete=models.CASCADE,
        related_name="procedures"
    )
    procedure_name = models.CharField(max_length=200)
    surgeon = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="surgery_procedures"
    )
    anesthesia_type = models.CharField(max_length=100, blank=True)
    operative_findings = models.TextField(blank=True)
    procedure_notes = models.TextField(blank=True)
    complications = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PLANNED"
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order"]),
            models.Index(fields=["surgeon"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.procedure_name} - {self.order.order_number}"


class SurgeryTeamMember(models.Model):
    ROLE_CHOICES = [
        ("SURGEON", "Surgeon"),
        ("ASSISTANT", "Assistant Surgeon"),
        ("ANESTHESIA", "Anesthesia"),
        ("NURSE", "Nurse"),
        ("TECHNICIAN", "Technician"),
        ("OTHER", "Other"),
    ]

    order = models.ForeignKey(
        SurgeryOrder,
        on_delete=models.CASCADE,
        related_name="team_members"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="surgery_team_memberships"
    )
    name = models.CharField(max_length=200)
    role = models.CharField(max_length=30, choices=ROLE_CHOICES)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["role", "name"]
        indexes = [
            models.Index(fields=["order"]),
            models.Index(fields=["role"]),
        ]

    def __str__(self):
        return f"{self.name} - {self.get_role_display()}"


class SurgeryPostoperativeNote(models.Model):
    order = models.ForeignKey(
        SurgeryOrder,
        on_delete=models.CASCADE,
        related_name="postoperative_notes"
    )
    recorded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="surgery_postoperative_notes"
    )
    condition = models.CharField(max_length=200, blank=True)
    vital_signs = models.TextField(blank=True)
    pain_score = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="0-10"
    )
    complications = models.TextField(blank=True)
    instructions = models.TextField(blank=True)
    note = models.TextField(blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-recorded_at"]
        indexes = [
            models.Index(fields=["order"]),
            models.Index(fields=["recorded_at"]),
        ]

    def __str__(self):
        return f"Postoperative Note - {self.order.order_number}"
