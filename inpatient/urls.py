from django.urls import path
from . import views

app_name = "inpatient"

urlpatterns = [
    path("", views.inpatient_dashboard, name="dashboard"),

    path("rooms/", views.room_list, name="room_list"),
    path("rooms/create/", views.room_create, name="room_create"),
    path("rooms/<int:room_id>/edit/", views.room_edit, name="room_edit"),

    path("beds/", views.bed_list, name="bed_list"),
    path("beds/create/", views.bed_create, name="bed_create"),

    path("admissions/", views.admission_list, name="admission_list"),
    path("admissions/create/", views.admission_create, name="admission_create"),
    path("api/patient-visits/", views.patient_visits_api, name="patient_visits_api"),
    path(
        "admissions/<int:admission_id>/",
        views.admission_detail,
        name="admission_detail",
    ),
    path(
        "admissions/<int:admission_id>/transfer/",
        views.admission_transfer,
        name="admission_transfer",
    ),
    path(
        "admissions/<int:admission_id>/discharge/",
        views.admission_discharge,
        name="admission_discharge",
    ),

    path(
        "admissions/<int:admission_id>/notes/create/",
        views.inpatient_note_create,
        name="note_create",
    ),

    path(
        "admissions/<int:admission_id>/vitals/create/",
        views.inpatient_vitals_create,
        name="vitals_create",
    ),

    path("search/", views.inpatient_search, name="search"),
]
