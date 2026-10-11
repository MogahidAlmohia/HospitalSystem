from django import forms

from .models import (
    NursingAssessment,
    VitalSigns,
    NursingNote,
    MedicationAdministration,
    NursingCarePlan,
)


class NursingAssessmentForm(forms.ModelForm):
    class Meta:
        model = NursingAssessment
        fields = [
            "patient",
            "visit",
            "chief_complaint",
            "medical_history",
            "nursing_diagnosis",
            "pain_score",
            "consciousness",
            "mobility",
            "nutrition_status",
            "fall_risk",
            "pressure_ulcer_risk",
            "status",
            "notes",
        ]

        widgets = {
            "patient": forms.Select(
                attrs={"class": "form-select"}
            ),
            "visit": forms.Select(
                attrs={"class": "form-select"}
            ),
            "chief_complaint": forms.Textarea(
                attrs={"class": "form-control", "rows": 2}
            ),
            "medical_history": forms.Textarea(
                attrs={"class": "form-control", "rows": 2}
            ),
            "nursing_diagnosis": forms.Textarea(
                attrs={"class": "form-control", "rows": 2}
            ),
            "pain_score": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                    "max": 10,
                }
            ),
            "consciousness": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "mobility": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "nutrition_status": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "fall_risk": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "pressure_ulcer_risk": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "status": forms.Select(
                attrs={"class": "form-select"}
            ),
            "notes": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
        }


class VitalSignsForm(forms.ModelForm):
    class Meta:
        model = VitalSigns
        fields = [
            "patient",
            "visit",
            "temperature",
            "pulse",
            "respiratory_rate",
            "systolic_bp",
            "diastolic_bp",
            "oxygen_saturation",
            "blood_glucose",
            "weight_kg",
            "height_cm",
            "pain_score",
            "notes",
        ]

        widgets = {
            "patient": forms.Select(
                attrs={"class": "form-select"}
            ),
            "visit": forms.Select(
                attrs={"class": "form-select"}
            ),
            "temperature": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.1",
                }
            ),
            "pulse": forms.NumberInput(
                attrs={"class": "form-control"}
            ),
            "respiratory_rate": forms.NumberInput(
                attrs={"class": "form-control"}
            ),
            "systolic_bp": forms.NumberInput(
                attrs={"class": "form-control"}
            ),
            "diastolic_bp": forms.NumberInput(
                attrs={"class": "form-control"}
            ),
            "oxygen_saturation": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                }
            ),
            "blood_glucose": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                }
            ),
            "weight_kg": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                }
            ),
            "height_cm": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                }
            ),
            "pain_score": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                    "max": 10,
                }
            ),
            "notes": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
        }


class NursingNoteForm(forms.ModelForm):
    class Meta:
        model = NursingNote
        fields = [
            "patient",
            "visit",
            "note_type",
            "note",
        ]

        widgets = {
            "patient": forms.Select(
                attrs={"class": "form-select"}
            ),
            "visit": forms.Select(
                attrs={"class": "form-select"}
            ),
            "note_type": forms.Select(
                attrs={"class": "form-select"}
            ),
            "note": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "اكتب ملاحظة التمريض...",
                }
            ),
        }


class MedicationAdministrationForm(forms.ModelForm):
    class Meta:
        model = MedicationAdministration
        fields = [
            "patient",
            "visit",
            "medicine_name",
            "dose",
            "route",
            "frequency",
            "administration_time",
            "status",
            "reason",
            "notes",
        ]

        widgets = {
            "patient": forms.Select(
                attrs={"class": "form-select"}
            ),
            "visit": forms.Select(
                attrs={"class": "form-select"}
            ),
            "medicine_name": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "dose": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "route": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "frequency": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "administration_time": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                }
            ),
            "status": forms.Select(
                attrs={"class": "form-select"}
            ),
            "reason": forms.Textarea(
                attrs={"class": "form-control", "rows": 2}
            ),
            "notes": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
        }


class NursingCarePlanForm(forms.ModelForm):
    class Meta:
        model = NursingCarePlan
        fields = [
            "patient",
            "visit",
            "problem",
            "goal",
            "interventions",
            "evaluation",
            "status",
        ]

        widgets = {
            "patient": forms.Select(
                attrs={"class": "form-select"}
            ),
            "visit": forms.Select(
                attrs={"class": "form-select"}
            ),
            "problem": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "goal": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "interventions": forms.Textarea(
                attrs={"class": "form-control", "rows": 4}
            ),
            "evaluation": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "status": forms.Select(
                attrs={"class": "form-select"}
            ),
        }
