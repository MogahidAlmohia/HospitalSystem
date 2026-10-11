from django.contrib import admin
from .models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = (
        "patient_number",
        "full_name",
        "gender",
        "phone",
        "blood_group",
        "is_active",
        "created_at",
    )

    search_fields = (
        "patient_number",
        "full_name",
        "phone",
        "national_id",
    )

    list_filter = (
        "gender",
        "blood_group",
        "is_active",
    )
