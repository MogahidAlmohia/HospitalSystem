from django.db import models
from django.contrib.auth.models import User
from departments.models import Department


class Doctor(models.Model):
    SPECIALTIES = [
        ("GENERAL", "General Medicine"),
        ("INTERNAL", "Internal Medicine"),
        ("PEDIATRICS", "Pediatrics"),
        ("SURGERY", "General Surgery"),
        ("OBGYN", "Obstetrics and Gynecology"),
        ("CARDIOLOGY", "Cardiology"),
        ("ORTHOPEDICS", "Orthopedics"),
        ("ENT", "ENT"),
        ("OPHTHALMOLOGY", "Ophthalmology"),
        ("DERMATOLOGY", "Dermatology"),
        ("DENTISTRY", "Dentistry"),
        ("EMERGENCY", "Emergency Medicine"),
        ("ANESTHESIA", "Anesthesiology"),
        ("RADIOLOGY", "Radiology"),
        ("OTHER", "Other"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="doctor_profile"
    )

    doctor_number = models.CharField(
        max_length=50,
        unique=True
    )

    full_name = models.CharField(
        max_length=200
    )

    specialty = models.CharField(
        max_length=30,
        choices=SPECIALTIES
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="doctors"
    )

    phone = models.CharField(
        max_length=30,
        blank=True
    )

    license_number = models.CharField(
        max_length=100,
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.doctor_number} - Dr. {self.full_name}"

    class Meta:
        ordering = ["full_name"]
