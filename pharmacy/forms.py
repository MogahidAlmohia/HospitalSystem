from django import forms

from .models import (
    Medicine,
    Prescription,
    PrescriptionItem,
)


class MedicineForm(forms.ModelForm):
    class Meta:
        model = Medicine
        fields = [
            "name_ar",
            "name_en",
            "generic_name",
            "code",
            "form",
            "strength",
            "unit",
            "manufacturer",
            "price",
            "stock_quantity",
            "reorder_level",
            "is_active",
        ]
        widgets = {
            "name_ar": forms.TextInput(attrs={"class": "form-control"}),
            "name_en": forms.TextInput(attrs={"class": "form-control"}),
            "generic_name": forms.TextInput(attrs={"class": "form-control"}),
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "form": forms.Select(attrs={"class": "form-select"}),
            "strength": forms.TextInput(attrs={"class": "form-control"}),
            "unit": forms.TextInput(attrs={"class": "form-control"}),
            "manufacturer": forms.TextInput(attrs={"class": "form-control"}),
            "price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "stock_quantity": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "reorder_level": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = [
            "patient",
            "visit",
            "doctor",
            "department",
            "diagnosis",
            "notes",
        ]
        widgets = {
            "patient": forms.Select(attrs={"class": "form-select"}),
            "visit": forms.Select(attrs={"class": "form-select"}),
            "doctor": forms.Select(attrs={"class": "form-select"}),
            "department": forms.Select(attrs={"class": "form-select"}),
            "diagnosis": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["patient"].queryset = (
            self.fields["patient"].queryset
            .filter(is_active=True)
            .order_by("full_name")
        )

        self.fields["doctor"].queryset = (
            self.fields["doctor"].queryset
            .filter(is_active=True)
            .order_by("full_name")
        )

        self.fields["department"].queryset = (
            self.fields["department"].queryset
            .filter(is_active=True)
            .order_by("name_ar")
        )


class PrescriptionItemForm(forms.ModelForm):
    class Meta:
        model = PrescriptionItem
        fields = [
            "medicine",
            "quantity",
            "dose",
            "frequency",
            "duration",
            "route",
            "instructions",
        ]
        widgets = {
            "medicine": forms.Select(attrs={"class": "form-select"}),
            "quantity": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0.01"}
            ),
            "dose": forms.TextInput(attrs={"class": "form-control"}),
            "frequency": forms.TextInput(attrs={"class": "form-control"}),
            "duration": forms.TextInput(attrs={"class": "form-control"}),
            "route": forms.TextInput(attrs={"class": "form-control"}),
            "instructions": forms.Textarea(
                attrs={"class": "form-control", "rows": 2}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["medicine"].queryset = (
            Medicine.objects
            .filter(is_active=True)
            .order_by("name_ar")
        )
