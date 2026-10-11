from django.db import models
from django.contrib.auth.models import User

from patients.models import Patient, Visit


class NursingAssessment(models.Model):
    STATUS_CHOICES = [
        ("OPEN", "Open"),
        ("IN_PROGRESS", "In Progress"),
        ("COMPLETED", "Completed"),
    ]

    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name="nursing_assessments",
    )

    visit = models.ForeignKey(
        Visit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="nursing_assessments",
    )

    nurse = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="nursing_assessments",
    )

    chief_complaint = models.TextField(blank=True)
    medical_history = models.TextField(blank=True)
    nursing_diagnosis = models.TextField(blank=True)

    pain_score = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="0-10",
    )

    consciousness = models.CharField(
        max_length=100,
        blank=True,
    )

    mobility = models.CharField(
        max_length=100,
        blank=True,
    )

    nutrition_status = models.CharField(
        max_length=100,
        blank=True,
    )

    fall_risk = models.BooleanField(default=False)
    pressure_ulcer_risk = models.BooleanField(default=False)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="OPEN",
    )

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["patient"]),
            models.Index(fields=["visit"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.patient.full_name} - Nursing Assessment"


class VitalSigns(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name="nursing_vital_signs",
    )

    visit = models.ForeignKey(
        Visit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="nursing_vital_signs",
    )

    recorded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_vital_signs",
    )

    temperature = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
    )

    pulse = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    respiratory_rate = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    systolic_bp = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    diastolic_bp = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    oxygen_saturation = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    blood_glucose = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )

    weight_kg = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )

    height_cm = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )

    pain_score = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="0-10",
    )

    notes = models.TextField(blank=True)

    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-recorded_at"]
        indexes = [
            models.Index(fields=["patient"]),
            models.Index(fields=["visit"]),
            models.Index(fields=["recorded_at"]),
        ]

    def __str__(self):
        return f"{self.patient.full_name} - Vital Signs"


class NursingNote(models.Model):
    NOTE_TYPES = [
        ("PROGRESS", "Progress Note"),
        ("OBSERVATION", "Observation"),
        ("HANDOVER", "Handover"),
        ("CARE", "Care Note"),
        ("OTHER", "Other"),
    ]

    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name="nursing_notes",
    )

    visit = models.ForeignKey(
        Visit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="nursing_notes",
    )

    nurse = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="nursing_notes",
    )

    note_type = models.CharField(
        max_length=20,
        choices=NOTE_TYPES,
        default="PROGRESS",
    )

    note = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["patient"]),
            models.Index(fields=["visit"]),
            models.Index(fields=["note_type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.patient.full_name} - Nursing Note"


class MedicationAdministration(models.Model):
    STATUS_CHOICES = [
        ("GIVEN", "Given"),
        ("HELD", "Held"),
        ("REFUSED", "Refused"),
        ("MISSED", "Missed"),
    ]

    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name="medication_administrations",
    )

    visit = models.ForeignKey(
        Visit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="medication_administrations",
    )

    administered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="medication_administrations",
    )

    medicine_name = models.CharField(
        max_length=200,
    )

    dose = models.CharField(
        max_length=100,
        blank=True,
    )

    route = models.CharField(
        max_length=100,
        blank=True,
    )

    frequency = models.CharField(
        max_length=100,
        blank=True,
    )

    administration_time = models.DateTimeField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="GIVEN",
    )

    reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-administration_time"]
        indexes = [
            models.Index(fields=["patient"]),
            models.Index(fields=["visit"]),
            models.Index(fields=["administration_time"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.patient.full_name} - {self.medicine_name}"


class NursingCarePlan(models.Model):
    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]

    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name="nursing_care_plans",
    )

    visit = models.ForeignKey(
        Visit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="nursing_care_plans",
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_nursing_care_plans",
    )

    problem = models.CharField(
        max_length=255,
    )

    goal = models.TextField(
        blank=True,
    )

    interventions = models.TextField(
        blank=True,
    )

    evaluation = models.TextField(
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["patient"]),
            models.Index(fields=["visit"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.patient.full_name} - {self.problem}"
