from django.urls import path

from . import views


app_name = "nursing"


urlpatterns = [
    path(
        "",
        views.dashboard,
        name="dashboard",
    ),

    path(
        "patients/",
        views.patient_list,
        name="patient_list",
    ),

    path(
        "patients/<int:patient_id>/",
        views.patient_record,
        name="patient_record",
    ),

    path(
        "assessments/create/",
        views.assessment_create,
        name="assessment_create",
    ),

    path(
        "vitals/create/",
        views.vital_signs_create,
        name="vitals_create",
    ),

    path(
        "notes/create/",
        views.note_create,
        name="note_create",
    ),

    path(
        "medications/create/",
        views.medication_create,
        name="medication_create",
    ),

    path(
        "care-plans/create/",
        views.care_plan_create,
        name="care_plan_create",
    ),
]
