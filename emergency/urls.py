from django.urls import path

from . import views

app_name = "reception"

urlpatterns = [
    path("", views.reception_dashboard, name="dashboard"),
    path("patients/register/", views.register_patient, name="register_patient"),
    path("patients/search/", views.patient_search, name="patient_search"),
    path("patients/<int:patient_id>/", views.patient_profile, name="patient_profile"),
    path(
        "patients/<int:patient_id>/visit/create/",
        views.create_visit,
        name="create_visit",
    ),
]


