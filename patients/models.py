from departments.models import Department
from doctors.models import Doctor
from django.db import models


class Patient(models.Model):
    GENDER_CHOICES = [
        ("M", "Male"),
        ("F", "Female"),
        ("O", "Other"),
    ]

    patient_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Patient Number"
    )

    full_name = models.CharField(
        max_length=200,
        verbose_name="Full Name"
    )

    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        verbose_name="Gender"
    )

    date_of_birth = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date of Birth"
    )

    age = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Age"
    )

    phone = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="Phone"
    )

    address = models.TextField(
        blank=True,
        verbose_name="Address"
    )

    national_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="National ID"
    )

    emergency_contact_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Emergency Contact Name"
    )

    emergency_contact_phone = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="Emergency Contact Phone"
    )

    blood_group = models.CharField(
        max_length=10,
        blank=True,
        verbose_name="Blood Group"
    )

    allergies = models.TextField(
        blank=True,
        verbose_name="Allergies"
    )

    medical_notes = models.TextField(
        blank=True,
        verbose_name="Medical Notes"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Active"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.patient_number} - {self.full_name}"

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Patient"
        verbose_name_plural = "Patients"
class Visit(models.Model):

    VISIT_TYPES = [
        ("OPD", "Outpatient"),
        ("ER", "Emergency"),
        ("INPATIENT", "Inpatient"),
        ("FOLLOWUP", "Follow-up"),
    ]

    STATUS_CHOICES = [
        ("OPEN", "Open"),
        ("IN_PROGRESS", "In Progress"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="visits"
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="visits"
    )

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="visits"
    )

    visit_number = models.CharField(
        max_length=50,
        unique=True
    )

    visit_type = models.CharField(
        max_length=20,
        choices=VISIT_TYPES,
        default="OPD"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="OPEN"
    )

    reason = models.TextField(
        blank=True
    )

    referring_doctor = models.CharField(
        max_length=200,
        blank=True
    )

    notes = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.visit_number} - {self.patient.full_name}"

    class Meta:
        ordering = ["-created_at"]

class ClinicalDiagnosis(models.Model):
    DIAGNOSIS_TYPES = [
        ("PRIMARY", "Primary"),
        ("SECONDARY", "Secondary"),
    ]

    STATUS_CHOICES = [
        ("SUSPECTED", "Suspected"),
        ("CONFIRMED", "Confirmed"),
        ("CHRONIC", "Chronic"),
        ("RESOLVED", "Resolved"),
    ]

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="clinical_diagnoses",
        verbose_name="Patient",
    )

    visit = models.ForeignKey(
        Visit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="clinical_diagnoses",
        verbose_name="Visit",
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="clinical_diagnoses",
        verbose_name="Department",
    )

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="clinical_diagnoses",
        verbose_name="Doctor",
    )

    diagnosis_name = models.CharField(
        max_length=300,
        verbose_name="Diagnosis",
    )

    diagnosis_name_en = models.CharField(
        max_length=300,
        blank=True,
        verbose_name="Diagnosis English",
    )

    icd10_code = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="ICD-10 Code",
    )

    diagnosis_type = models.CharField(
        max_length=20,
        choices=DIAGNOSIS_TYPES,
        default="PRIMARY",
        verbose_name="Diagnosis Type",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="CONFIRMED",
        verbose_name="Status",
    )

    is_chronic = models.BooleanField(
        default=False,
        verbose_name="Chronic Disease",
    )

    notes = models.TextField(
        blank=True,
        verbose_name="Clinical Notes",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.patient.full_name} - {self.diagnosis_name}"

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Clinical Diagnosis"
        verbose_name_plural = "Clinical Diagnoses"
