from django.db import models
from django.contrib.auth.models import User

from patients.models import Patient, Visit
from doctors.models import Doctor
from departments.models import Department


class RadiologyExamType(models.Model):
    name_ar = models.CharField(
        max_length=200,
        verbose_name="اسم الفحص بالعربي"
    )

    name_en = models.CharField(
        max_length=200,
        verbose_name="Exam Name"
    )

    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Exam Code"
    )

    modality = models.CharField(
        max_length=50,
        choices=[
            ("XRAY", "X-Ray"),
            ("US", "Ultrasound"),
            ("CT", "CT Scan"),
            ("MRI", "MRI"),
            ("MAMMO", "Mammography"),
            ("FLUORO", "Fluoroscopy"),
            ("OTHER", "Other"),
        ],
        default="XRAY",
        verbose_name="Modality"
    )

    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Price"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Active"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name_ar"]
        verbose_name = "Radiology Exam Type"
        verbose_name_plural = "Radiology Exam Types"

    def __str__(self):
        return f"{self.name_ar} - {self.name_en}"


class RadiologyOrder(models.Model):

    PRIORITY_CHOICES = [
        ("NORMAL", "Normal"),
        ("URGENT", "Urgent"),
        ("STAT", "STAT"),
    ]

    STATUS_CHOICES = [
        ("REQUESTED", "Requested"),
        ("SCHEDULED", "Scheduled"),
        ("IN_PROGRESS", "In Progress"),
        ("COMPLETED", "Completed"),
        ("REPORTED", "Reported"),
        ("DELIVERED", "Delivered"),
        ("CANCELLED", "Cancelled"),
    ]

    order_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Radiology Order Number"
    )

    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name="radiology_orders",
        verbose_name="Patient"
    )

    visit = models.ForeignKey(
        Visit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="radiology_orders",
        verbose_name="Visit"
    )

    requesting_doctor = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="radiology_orders",
        verbose_name="Requesting Doctor"
    )

    requesting_department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="radiology_orders",
        verbose_name="Requesting Department"
    )

    exam_type = models.ForeignKey(
        RadiologyExamType,
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name="Exam Type"
    )

    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default="NORMAL",
        verbose_name="Priority"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="REQUESTED",
        verbose_name="Status"
    )

    clinical_indication = models.TextField(
        blank=True,
        verbose_name="Clinical Indication"
    )

    preparation_notes = models.TextField(
        blank=True,
        verbose_name="Preparation Notes"
    )

    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Scheduled At"
    )

    performed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Performed At"
    )

    report_text = models.TextField(
        blank=True,
        verbose_name="Radiology Report"
    )

    report_impression = models.TextField(
        blank=True,
        verbose_name="Impression"
    )

    reported_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="radiology_reports",
        verbose_name="Reported By"
    )

    requested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="radiology_requests",
        verbose_name="Requested By"
    )

    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Delivered At"
    )

    notes = models.TextField(
        blank=True,
        verbose_name="Notes"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Radiology Order"
        verbose_name_plural = "Radiology Orders"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["priority"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["patient"]),
        ]

    def save(self, *args, **kwargs):
        if not self.order_number:
            from django.utils import timezone

            today = timezone.localdate().strftime("%Y%m%d")
            prefix = f"RAD-{today}-"

            last = (
                RadiologyOrder.objects
                .filter(order_number__startswith=prefix)
                .exclude(pk=self.pk)
                .order_by("-id")
                .first()
            )

            number = 1

            if last and last.order_number:
                try:
                    number = int(last.order_number.split("-")[-1]) + 1
                except (ValueError, IndexError):
                    number = 1

            self.order_number = f"{prefix}{number:04d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_number} - {self.patient.full_name}"
