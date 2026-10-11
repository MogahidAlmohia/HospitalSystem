from django import forms

from .models import (
    SurgeryType,
    SurgeryOrder,
    SurgeryProcedure,
    SurgeryTeamMember,
    SurgeryPostoperativeNote,
)


class BootstrapModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"
            else:
                existing = field.widget.attrs.get("class", "")
                field.widget.attrs["class"] = (
                    f"{existing} form-control".strip()
                )

            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("placeholder", field.label)


class SurgeryTypeForm(BootstrapModelForm):
    class Meta:
        model = SurgeryType
        fields = [
            "name_ar",
            "name_en",
            "code",
            "specialty",
            "estimated_duration_minutes",
            "is_active",
        ]

    def clean_code(self):
        code = self.cleaned_data["code"].strip().upper()
        if not code:
            raise forms.ValidationError("كود العملية مطلوب.")
        return code


class SurgeryOrderForm(BootstrapModelForm):
    class Meta:
        model = SurgeryOrder
        fields = [
            "patient",
            "visit",
            "surgery_type",
            "surgeon",
            "priority",
            "status",
            "diagnosis",
            "indication",
            "preoperative_notes",
            "notes",
            "scheduled_at",
        ]
        widgets = {
            "diagnosis": forms.Textarea(attrs={"rows": 3}),
            "indication": forms.Textarea(attrs={"rows": 3}),
            "preoperative_notes": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
            "scheduled_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"}
            ),
        }

    def clean(self):
        cleaned = super().clean()

        patient = cleaned.get("patient")
        visit = cleaned.get("visit")

        if visit and patient and visit.patient_id != patient.id:
            raise forms.ValidationError(
                "الزيارة المحددة لا تخص المريض المحدد."
            )

        return cleaned


class SurgeryProcedureForm(BootstrapModelForm):
    class Meta:
        model = SurgeryProcedure
        fields = [
            "order",
            "procedure_name",
            "surgeon",
            "anesthesia_type",
            "operative_findings",
            "procedure_notes",
            "complications",
            "status",
            "started_at",
            "completed_at",
        ]
        widgets = {
            "operative_findings": forms.Textarea(attrs={"rows": 4}),
            "procedure_notes": forms.Textarea(attrs={"rows": 4}),
            "complications": forms.Textarea(attrs={"rows": 3}),
            "started_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"}
            ),
            "completed_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"}
            ),
        }

    def clean(self):
        cleaned = super().clean()

        started = cleaned.get("started_at")
        completed = cleaned.get("completed_at")

        if started and completed and completed < started:
            raise forms.ValidationError(
                "وقت انتهاء العملية لا يمكن أن يسبق وقت بدايتها."
            )

        return cleaned


class SurgeryTeamMemberForm(BootstrapModelForm):
    class Meta:
        model = SurgeryTeamMember
        fields = [
            "order",
            "user",
            "name",
            "role",
            "notes",
        ]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class SurgeryPostoperativeNoteForm(BootstrapModelForm):
    class Meta:
        model = SurgeryPostoperativeNote
        fields = [
            "order",
            "condition",
            "vital_signs",
            "pain_score",
            "complications",
            "instructions",
            "note",
        ]
        widgets = {
            "vital_signs": forms.Textarea(attrs={"rows": 3}),
            "complications": forms.Textarea(attrs={"rows": 3}),
            "instructions": forms.Textarea(attrs={"rows": 3}),
            "note": forms.Textarea(attrs={"rows": 4}),
        }

    def clean_pain_score(self):
        value = self.cleaned_data.get("pain_score")

        if value is not None and not 0 <= value <= 10:
            raise forms.ValidationError(
                "درجة الألم يجب أن تكون بين 0 و10."
            )

        return value
