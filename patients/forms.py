from django import forms
from django.core.exceptions import ValidationError
from .models import Patient, Visit
from departments.models import Department
from doctors.models import Doctor


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = [
            "patient_number",
            "full_name",
            "gender",
            "date_of_birth",
            "age",
            "phone",
            "address",
            "national_id",
            "emergency_contact_name",
            "emergency_contact_phone",
            "blood_group",
            "allergies",
            "medical_notes",
            "is_active",
        ]

        widgets = {
            "patient_number": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "رقم المريض"}
            ),
            "full_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "اسم المريض"}
            ),
            "gender": forms.Select(attrs={"class": "form-select"}),
            "date_of_birth": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "age": forms.NumberInput(
                attrs={"class": "form-control", "min": "0"}
            ),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(
                attrs={"class": "form-control", "rows": 2}
            ),
            "national_id": forms.TextInput(attrs={"class": "form-control"}),
            "emergency_contact_name": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "emergency_contact_phone": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "blood_group": forms.TextInput(attrs={"class": "form-control"}),
            "allergies": forms.Textarea(
                attrs={"class": "form-control", "rows": 2}
            ),
            "medical_notes": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "is_active": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }


class VisitForm(forms.ModelForm):
    class Meta:
        model = Visit
        fields = [
            "department",
            "doctor",
            "visit_number",
            "visit_type",
            "status",
            "reason",
            "referring_doctor",
            "notes",
        ]

        widgets = {
            "department": forms.Select(
                attrs={"class": "form-select", "id": "id_department"}
            ),
            "doctor": forms.Select(
                attrs={"class": "form-select", "id": "id_doctor"}
            ),
            "visit_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "رقم الزيارة اليدوي",
                }
            ),
            "visit_type": forms.Select(
                attrs={"class": "form-select"}
            ),
            "status": forms.Select(
                attrs={"class": "form-select"}
            ),
            "reason": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "referring_doctor": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "notes": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
        }

    def __init__(self, *args, **kwargs):
        fixed_department = kwargs.pop("fixed_department", None)
        super().__init__(*args, **kwargs)

        self.fields["department"].queryset = Department.objects.filter(
            is_active=True
        ).order_by("name_en")

        self.fields["doctor"].queryset = Doctor.objects.filter(
            is_active=True
        ).select_related("department").order_by("full_name")

        if fixed_department is not None:
            self.fields["department"].queryset = Department.objects.filter(
                pk=fixed_department.pk,
                is_active=True,
            )
            self.fields["department"].initial = fixed_department.pk
            self.fields["department"].disabled = True

    def clean(self):
        cleaned = super().clean()

        department = cleaned.get("department")
        doctor = cleaned.get("doctor")

        if doctor and department:
            if doctor.department_id != department.id:
                raise ValidationError(
                    "الطبيب المختار لا يتبع القسم المحدد."
                )

        return cleaned

class ClinicalDiagnosisForm(forms.ModelForm):
    class Meta:
        model = __import__("patients.models", fromlist=["ClinicalDiagnosis"]).ClinicalDiagnosis
        fields = [
            "diagnosis_name",
            "diagnosis_name_en",
            "icd10_code",
            "diagnosis_type",
            "status",
            "is_chronic",
            "notes",
        ]
        widgets = {
            "diagnosis_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "اسم المرض أو التشخيص",
                    "required": True,
                }
            ),
            "diagnosis_name_en": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Diagnosis name in English",
                }
            ),
            "icd10_code": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "ICD-10",
                }
            ),
            "diagnosis_type": forms.Select(
                attrs={"class": "form-select"}
            ),
            "status": forms.Select(
                attrs={"class": "form-select"}
            ),
            "is_chronic": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "ملاحظات سريرية",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        self.department = kwargs.pop("department", None)
        self.doctor = kwargs.pop("doctor", None)
        self.patient = kwargs.pop("patient", None)
        self.visit = kwargs.pop("visit", None)
        super().__init__(*args, **kwargs)
