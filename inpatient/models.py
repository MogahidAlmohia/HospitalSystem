from django.db import models
from django.contrib.auth.models import User
from patients.models import Patient, Visit
from departments.models import Department
from doctors.models import Doctor


class Room(models.Model):
    ROOM_TYPES = [
        ("GENERAL", "General Ward"),
        ("PRIVATE", "Private Room"),
        ("ICU", "ICU"),
        ("NICU", "NICU"),
        ("PICU", "PICU"),
        ("ISOLATION", "Isolation"),
        ("MATERNITY", "Maternity"),
        ("SURGERY", "Surgical Ward"),
        ("OTHER", "Other"),
    ]

    name = models.CharField(max_length=100)
    room_number = models.CharField(max_length=50, unique=True)
    room_type = models.CharField(
        max_length=30,
        choices=ROOM_TYPES,
        default="GENERAL",
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inpatient_rooms",
    )
    floor = models.CharField(max_length=50, blank=True)
    capacity = models.PositiveIntegerField(default=1)
    phone = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["room_number"]

    def __str__(self):
        return f"{self.room_number} - {self.name}"


class Bed(models.Model):
    STATUS_CHOICES = [
        ("AVAILABLE", "Available"),
        ("OCCUPIED", "Occupied"),
        ("RESERVED", "Reserved"),
        ("MAINTENANCE", "Maintenance"),
        ("INACTIVE", "Inactive"),
    ]

    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name="beds",
    )
    bed_number = models.CharField(max_length=50)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="AVAILABLE",
    )
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["room__room_number", "bed_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["room", "bed_number"],
                name="unique_bed_per_room",
            )
        ]

    def __str__(self):
        return f"{self.room.room_number} / {self.bed_number}"


class Admission(models.Model):
    STATUS_CHOICES = [
        ("ADMITTED", "Admitted"),
        ("TRANSFERRED", "Transferred"),
        ("DISCHARGED", "Discharged"),
        ("CANCELLED", "Cancelled"),
    ]

    ADMISSION_TYPES = [
        ("EMERGENCY", "Emergency"),
        ("ELECTIVE", "Elective"),
        ("REFERRAL", "Referral"),
        ("OTHER", "Other"),
    ]

    admission_number = models.CharField(
        max_length=50,
        unique=True,
    )

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="admissions",
    )

    visit = models.ForeignKey(
        Visit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admissions",
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admissions",
    )

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admissions",
    )

    room = models.ForeignKey(
        Room,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admissions",
    )

    bed = models.ForeignKey(
        Bed,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admissions",
    )

    admission_type = models.CharField(
        max_length=20,
        choices=ADMISSION_TYPES,
        default="EMERGENCY",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ADMITTED",
    )

    admission_diagnosis = models.TextField(
        blank=True,
        verbose_name="Admission Diagnosis",
    )

    clinical_notes = models.TextField(blank=True)

    admitted_at = models.DateTimeField(
        auto_now_add=True,
    )

    expected_discharge_date = models.DateField(
        null=True,
        blank=True,
    )

    discharged_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    discharge_diagnosis = models.TextField(blank=True)

    discharge_notes = models.TextField(blank=True)

    discharge_type = models.CharField(
        max_length=30,
        blank=True,
    )

    admitted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inpatient_admissions_created",
    )

    discharged_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inpatient_discharges",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-admitted_at"]

    def __str__(self):
        return f"{self.admission_number} - {self.patient.full_name}"


class BedTransfer(models.Model):
    admission = models.ForeignKey(
        Admission,
        on_delete=models.CASCADE,
        related_name="bed_transfers",
    )

    from_room = models.ForeignKey(
        Room,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transfers_from",
    )

    from_bed = models.ForeignKey(
        Bed,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transfers_from",
    )

    to_room = models.ForeignKey(
        Room,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transfers_to",
    )

    to_bed = models.ForeignKey(
        Bed,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transfers_to",
    )

    reason = models.TextField(blank=True)

    transferred_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inpatient_bed_transfers",
    )

    transferred_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-transferred_at"]


class InpatientNote(models.Model):
    NOTE_TYPES = [
        ("DOCTOR", "Doctor Note"),
        ("NURSING", "Nursing Note"),
        ("PROGRESS", "Progress Note"),
        ("OTHER", "Other"),
    ]

    admission = models.ForeignKey(
        Admission,
        on_delete=models.CASCADE,
        related_name="notes",
    )

    note_type = models.CharField(
        max_length=20,
        choices=NOTE_TYPES,
        default="PROGRESS",
    )

    note = models.TextField()

    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inpatient_notes",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class InpatientVitalSign(models.Model):
    admission = models.ForeignKey(
        Admission,
        on_delete=models.CASCADE,
        related_name="vital_signs",
    )

    temperature = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    pulse = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    respiratory_rate = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    systolic_bp = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    diastolic_bp = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    oxygen_saturation = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    pain_score = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    recorded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inpatient_vital_signs",
    )

    recorded_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-recorded_at"]
