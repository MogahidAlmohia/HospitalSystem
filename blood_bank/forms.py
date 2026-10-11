from django import forms

from patients.models import Patient, Visit
from doctors.models import Doctor
from departments.models import Department

from .models import (
    BloodDonor,
    BloodUnit,
    BloodRequest,
    BloodCrossmatch,
)


class BloodDonorForm(forms.ModelForm):
    class Meta:
        model = BloodDonor
        fields = [
            "donor_number",
            "full_name",
            "national_id",
            "blood_group",
            "phone",
            "date_of_birth",
            "address",
            "last_donation_date",
            "is_active",
            "notes",
        ]
        widgets = {
            "donor_number": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "full_name": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "national_id": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "blood_group": forms.Select(
                attrs={"class": "form-select"}
            ),
            "phone": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "date_of_birth": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "address": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                }
            ),
            "last_donation_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
        }


class BloodUnitForm(forms.ModelForm):
    class Meta:
        model = BloodUnit
        fields = [
            "unit_number",
            "donor",
            "blood_group",
            "component",
            "collection_date",
            "expiry_date",
            "volume_ml",
            "status",
            "storage_location",
            "screening_result",
            "notes",
        ]
        widgets = {
            "unit_number": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "donor": forms.Select(
                attrs={"class": "form-select"}
            ),
            "blood_group": forms.Select(
                attrs={"class": "form-select"}
            ),
            "component": forms.Select(
                attrs={"class": "form-select"}
            ),
            "collection_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "expiry_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "volume_ml": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "1",
                }
            ),
            "status": forms.Select(
                attrs={"class": "form-select"}
            ),
            "storage_location": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "screening_result": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["donor"].queryset = (
            BloodDonor.objects
            .filter(is_active=True)
            .order_by("full_name")
        )


class BloodRequestForm(forms.ModelForm):
    class Meta:
        model = BloodRequest
        fields = [
            "patient",
            "visit",
            "requesting_doctor",
            "requesting_department",
            "patient_blood_group",
            "component",
            "units_requested",
            "priority",
            "indication",
            "notes",
        ]
        widgets = {
            "patient": forms.Select(
                attrs={"class": "form-select"}
            ),
            "visit": forms.Select(
                attrs={"class": "form-select"}
            ),
            "requesting_doctor": forms.Select(
                attrs={"class": "form-select"}
            ),
            "requesting_department": forms.Select(
                attrs={"class": "form-select"}
            ),
            "patient_blood_group": forms.Select(
                attrs={"class": "form-select"}
            ),
            "component": forms.Select(
                attrs={"class": "form-select"}
            ),
            "units_requested": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "1",
                }
            ),
            "priority": forms.Select(
                attrs={"class": "form-select"}
            ),
            "indication": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["patient"].queryset = (
            Patient.objects
            .filter(is_active=True)
            .order_by("full_name")
        )

        self.fields["visit"].queryset = (
            Visit.objects
            .select_related("patient")
            .order_by("-created_at")
        )

        self.fields["requesting_doctor"].queryset = (
            Doctor.objects
            .filter(is_active=True)
            .order_by("full_name")
        )

        self.fields["requesting_department"].queryset = (
            Department.objects
            .filter(is_active=True)
            .order_by("name_ar")
        )


class BloodIssueForm(forms.Form):
    blood_unit = forms.ModelChoiceField(
        queryset=BloodUnit.objects.none(),
        label="وحدة الدم",
        widget=forms.Select(
            attrs={"class": "form-select"}
        ),
    )

    notes = forms.CharField(
        required=False,
        label="ملاحظات",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["blood_unit"].queryset = (
            BloodUnit.objects
            .filter(status="AVAILABLE")
            .order_by(
                "expiry_date",
                "blood_group",
                "unit_number",
            )
        )


class BloodTransfusionForm(forms.Form):
    status = forms.ChoiceField(
        choices=[
            ("STARTED", "بدأ نقل الدم"),
            ("COMPLETED", "اكتمل نقل الدم"),
            ("STOPPED", "تم إيقاف النقل"),
            ("REACTION", "حدث تفاعل"),
        ],
        widget=forms.Select(
            attrs={"class": "form-select"}
        ),
        label="الحالة",
    )

    reaction_notes = forms.CharField(
        required=False,
        label="ملاحظات التفاعل",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
            }
        ),
    )

    notes = forms.CharField(
        required=False,
        label="ملاحظات",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
            }
        ),
    )


class BloodCrossmatchForm(forms.ModelForm):
    class Meta:
        model = BloodCrossmatch
        fields = [
            "blood_unit",
            "result",
            "notes",
        ]
        widgets = {
            "blood_unit": forms.Select(
                attrs={"class": "form-select"}
            ),
            "result": forms.Select(
                attrs={"class": "form-select"}
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "ملاحظات اختبار التوافق...",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        request_obj = kwargs.pop("blood_request", None)
        super().__init__(*args, **kwargs)

        if request_obj is not None:
            self.fields["blood_unit"].queryset = (
                BloodUnit.objects
                .filter(
                    status="AVAILABLE",
                    component=request_obj.component,
                )
                .select_related("donor")
                .order_by("unit_number")
            )
