from django.db import models
from django.contrib.auth.models import User
from patients.models import Patient, Visit
from doctors.models import Doctor
from departments.models import Department


class Medicine(models.Model):
    FORM_CHOICES = [
        ("TABLET", "Tablet"),
        ("CAPSULE", "Capsule"),
        ("SYRUP", "Syrup"),
        ("INJECTION", "Injection"),
        ("CREAM", "Cream"),
        ("OINTMENT", "Ointment"),
        ("DROPS", "Drops"),
        ("INHALER", "Inhaler"),
        ("SUPPOSITORY", "Suppository"),
        ("OTHER", "Other"),
    ]

    name_ar = models.CharField(
        max_length=200,
        verbose_name="اسم الدواء بالعربي"
    )
    name_en = models.CharField(
        max_length=200,
        verbose_name="Medicine Name"
    )
    generic_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Generic Name"
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Medicine Code"
    )
    form = models.CharField(
        max_length=30,
        choices=FORM_CHOICES,
        default="TABLET",
        verbose_name="Dosage Form"
    )
    strength = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Strength"
    )
    unit = models.CharField(
        max_length=50,
        default="علبة",
        verbose_name="Unit"
    )
    manufacturer = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Manufacturer"
    )
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Price"
    )
    stock_quantity = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name="Stock Quantity"
    )
    reorder_level = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name="Reorder Level"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name_ar"]
        verbose_name = "Medicine"
        verbose_name_plural = "Medicines"
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["name_ar"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.name_ar} - {self.name_en}"


class Prescription(models.Model):
    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("PENDING", "Pending"),
        ("PARTIALLY_DISPENSED", "Partially Dispensed"),
        ("DISPENSED", "Dispensed"),
        ("CANCELLED", "Cancelled"),
    ]

    prescription_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Prescription Number"
    )
    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name="prescriptions",
        verbose_name="Patient"
    )
    visit = models.ForeignKey(
        Visit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prescriptions",
        verbose_name="Visit"
    )
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prescriptions",
        verbose_name="Doctor"
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prescriptions",
        verbose_name="Department"
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="PENDING",
        verbose_name="Status"
    )
    diagnosis = models.TextField(
        blank=True,
        verbose_name="Diagnosis"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Notes"
    )
    prescribed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pharmacy_prescriptions",
        verbose_name="Prescribed By"
    )
    dispensed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pharmacy_dispensed_prescriptions",
        verbose_name="Dispensed By"
    )
    dispensed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Dispensed At"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Prescription"
        verbose_name_plural = "Prescriptions"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["patient"]),
        ]

    def __str__(self):
        return f"{self.prescription_number} - {self.patient.full_name}"

    def save(self, *args, **kwargs):
        if not self.prescription_number:
            from django.utils import timezone

            today = timezone.localdate().strftime("%Y%m%d")
            prefix = f"RX-{today}-"

            last = (
                Prescription.objects
                .filter(prescription_number__startswith=prefix)
                .exclude(pk=self.pk)
                .order_by("-id")
                .first()
            )

            number = 1

            if last and last.prescription_number:
                try:
                    number = (
                        int(last.prescription_number.split("-")[-1]) + 1
                    )
                except (ValueError, IndexError):
                    number = 1

            self.prescription_number = f"{prefix}{number:04d}"

        super().save(*args, **kwargs)


class PrescriptionItem(models.Model):
    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Prescription"
    )
    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.PROTECT,
        related_name="prescription_items",
        verbose_name="Medicine"
    )
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=1,
        verbose_name="Quantity"
    )
    dose = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Dose"
    )
    frequency = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Frequency"
    )
    duration = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Duration"
    )
    route = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Route"
    )
    instructions = models.TextField(
        blank=True,
        verbose_name="Instructions"
    )
    dispensed_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Dispensed Quantity"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        verbose_name = "Prescription Item"
        verbose_name_plural = "Prescription Items"

    def __str__(self):
        return f"{self.prescription.prescription_number} - {self.medicine.name_ar}"


class PharmacyStockMovement(models.Model):
    MOVEMENT_CHOICES = [
        ("IN", "Stock In"),
        ("OUT", "Stock Out"),
        ("ADJUSTMENT", "Adjustment"),
    ]

    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.PROTECT,
        related_name="stock_movements",
        verbose_name="Medicine"
    )
    movement_type = models.CharField(
        max_length=20,
        choices=MOVEMENT_CHOICES,
        verbose_name="Movement Type"
    )
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Quantity"
    )
    balance_after = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name="Balance After"
    )
    reference = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Reference"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Notes"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pharmacy_stock_movements",
        verbose_name="Created By"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Pharmacy Stock Movement"
        verbose_name_plural = "Pharmacy Stock Movements"
        indexes = [
            models.Index(fields=["medicine"]),
            models.Index(fields=["movement_type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.medicine.name_ar} - {self.movement_type} - {self.quantity}"
