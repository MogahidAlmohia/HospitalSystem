from decimal import Decimal

from django import forms

from patients.models import Patient, Visit
from .models import Bill, BillItem, BillPayment


class BootstrapModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (
                f"{existing} form-control".strip()
            )

            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = (
                    f"{existing} form-select".strip()
                )


class BillForm(BootstrapModelForm):
    class Meta:
        model = Bill
        fields = [
            "patient",
            "visit",
            "payment_method",
            "discount",
            "notes",
        ]

        widgets = {
            "patient": forms.Select(),
            "visit": forms.Select(),
            "payment_method": forms.Select(),
            "discount": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "rows": 3,
                }
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

        self.fields["visit"].required = False

    def clean(self):
        cleaned_data = super().clean()

        patient = cleaned_data.get("patient")
        visit = cleaned_data.get("visit")

        if patient and visit and visit.patient_id != patient.id:
            raise forms.ValidationError(
                "الزيارة المحددة لا تتبع للمريض المحدد."
            )

        discount = cleaned_data.get("discount") or Decimal("0.00")

        if discount < Decimal("0.00"):
            self.add_error(
                "discount",
                "الخصم لا يمكن أن يكون سالباً.",
            )

        return cleaned_data


class BillItemForm(BootstrapModelForm):
    class Meta:
        model = BillItem
        fields = [
            "service_type",
            "description",
            "quantity",
            "unit_price",
            "notes",
        ]

        widgets = {
            "service_type": forms.Select(),
            "description": forms.TextInput(),
            "quantity": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "min": "0.01",
                }
            ),
            "unit_price": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "notes": forms.TextInput(),
        }

    def clean(self):
        cleaned_data = super().clean()

        quantity = cleaned_data.get("quantity")
        unit_price = cleaned_data.get("unit_price")

        if quantity is not None and quantity <= 0:
            self.add_error(
                "quantity",
                "الكمية يجب أن تكون أكبر من صفر.",
            )

        if unit_price is not None and unit_price < 0:
            self.add_error(
                "unit_price",
                "سعر الوحدة لا يمكن أن يكون سالباً.",
            )

        return cleaned_data


class BillPaymentForm(BootstrapModelForm):
    class Meta:
        model = BillPayment
        fields = [
            "amount",
            "payment_method",
            "reference",
            "notes",
        ]

        widgets = {
            "amount": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "min": "0.01",
                }
            ),
            "payment_method": forms.Select(),
            "reference": forms.TextInput(),
            "notes": forms.TextInput(),
        }

    def __init__(self, *args, **kwargs):
        self.bill = kwargs.pop("bill", None)
        super().__init__(*args, **kwargs)

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")

        if amount is None:
            return amount

        if amount <= 0:
            raise forms.ValidationError(
                "مبلغ الدفعة يجب أن يكون أكبر من صفر."
            )

        if self.bill is not None:
            remaining = self.bill.remaining_amount

            if amount > remaining:
                raise forms.ValidationError(
                    f"مبلغ الدفعة ({amount}) أكبر من المبلغ المتبقي "
                    f"({remaining})."
                )

        return amount
