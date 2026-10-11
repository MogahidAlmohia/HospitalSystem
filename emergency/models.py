from django.db import models
from django.contrib.auth.models import User
from patients.models import Patient
from departments.models import Department
from doctors.models import Doctor


class EmergencyCase(models.Model):

    TRIAGE_CHOICES = [
        ("RED", "Red - Immediate"),
        ("ORANGE", "Orange - Very Urgent"),
        ("YELLOW", "Yellow - Urgent"),
        ("GREEN", "Green - Less Urgent"),
        ("BLUE", "Blue - Non Urgent"),
    ]

    STATUS_CHOICES = [
        ("WAITING", "Waiting"),
        ("TRIAGE", "Triage"),
        ("UNDER_CARE", "Under Care"),
        ("OBSERVATION", "Observation"),
        ("ADMITTED", "Admitted"),
        ("TRANSFERRED", "Transferred"),
        ("DISCHARGED", "Discharged"),
        ("CANCELLED", "Cancelled"),
    ]

    DISPOSITION_CHOICES = [
        ("HOME", "Discharged Home"),
        ("INPATIENT", "Admitted"),
        ("TRANSFER", "Transferred"),
        ("OBSERVATION", "Observation"),
        ("LEFT", "Left Without Treatment"),
        ("OTHER", "Other"),
    ]

    case_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Emergency Case Number",
    )

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="emergency_cases",
    )

    visit = models.ForeignKey(
        "patients.Visit",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="emergency_cases",
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="emergency_cases",
    )

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="emergency_cases",
    )

    triage_level = models.CharField(
        max_length=20,
        choices=TRIAGE_CHOICES,
        default="YELLOW",
    )

    chief_complaint = models.TextField(
        verbose_name="Chief Complaint",
    )

    history = models.TextField(
        blank=True,
        verbose_name="History",
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

    preliminary_diagnosis = models.TextField(
        blank=True,
    )

    treatment = models.TextField(
        blank=True,
    )

    clinical_notes = models.TextField(
        blank=True,
    )

    disposition = models.CharField(
        max_length=30,
        choices=DISPOSITION_CHOICES,
        blank=True,
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="WAITING",
    )

    registered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="registered_emergency_cases",
    )

    arrival_at = models.DateTimeField(
        auto_now_add=True,
    )

    treated_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    discharged_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-arrival_at"]

    def __str__(self):
        return f"{self.case_number} - {self.patient.full_name}"
