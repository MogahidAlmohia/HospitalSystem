from django.db import models
from patients.models import Patient, Visit


class ReceptionRecord(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="reception_records"
    )

    visit = models.OneToOneField(
        Visit,
        on_delete=models.CASCADE,
        related_name="reception_record"
    )

    arrival_time = models.DateTimeField(
        auto_now_add=True
    )

    registration_notes = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.patient.full_name} - {self.visit.visit_number}"
