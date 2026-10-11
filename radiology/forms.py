from django import forms

from .models import RadiologyExamType, RadiologyOrder
from patients.models import Patient, Visit
from doctors.models import Doctor
from departments.models import Department


class RadiologyOrderForm(forms.ModelForm):
    class Meta:
        model = RadiologyOrder
        fields = [
            "patient",
            "visit",
            "requesting_doctor",
            "requesting_department",
            "exam_type",
            "priority",
            "clinical_indication",
            "preparation_notes",
            "notes",
        ]

        widgets = {
            "patient": forms.Select(attrs={"class": "form-select"}),
            "visit": forms.Select(attrs={"class": "form-select"}),
            "requesting_doctor": forms.Select(attrs={"class": "form-select"}),
            "requesting_department": forms.Select(attrs={"class": "form-select"}),
            "exam_type": forms.Select(attrs={"class": "form-select"}),
            "priority": forms.Select(attrs={"class": "form-select"}),
            "clinical_indication": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "preparation_notes": forms.Textarea(
                attrs={"class": "form-control", "rows": 2}
            ),
            "notes": forms.Textarea(
                attrs={"class": "form-control", "rows": 2}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["patient"].queryset = Patient.objects.filter(
            is_active=True
        ).order_by("full_name")

        self.fields["visit"].queryset = Visit.objects.select_related(
            "patient"
        ).order_by("-created_at")

        self.fields["requesting_doctor"].queryset = Doctor.objects.filter(
            is_active=True
        ).order_by("full_name")

        self.fields["requesting_department"].queryset = Department.objects.filter(
            is_active=True
        ).order_by("name_ar")

        self.fields["exam_type"].queryset = RadiologyExamType.objects.filter(
            is_active=True
        ).order_by("name_ar")


class RadiologyReportForm(forms.ModelForm):
    class Meta:
        model = RadiologyOrder
        fields = [
            "status",
            "report_text",
            "report_impression",
            "notes",
        ]

        widgets = {
            "status": forms.Select(attrs={"class": "form-select"}),
            "report_text": forms.Textarea(
                attrs={"class": "form-control", "rows": 8}
            ),
            "report_impression": forms.Textarea(
                attrs={"class": "form-control", "rows": 4}
            ),
            "notes": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
        }


class RadiologyExamTypeForm(forms.ModelForm):
    class Meta:
        model = RadiologyExamType
        fields = [
            "name_ar",
            "name_en",
            "code",
            "modality",
            "description",
            "price",
            "is_active",
        ]

        widgets = {
            "name_ar": forms.TextInput(attrs={"class": "form-control"}),
            "name_en": forms.TextInput(attrs={"class": "form-control"}),
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "modality": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "price": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
            "is_active": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }
