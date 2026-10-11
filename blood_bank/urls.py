from django.urls import path

from . import views


app_name = "blood_bank"


urlpatterns = [
    path(
        "",
        views.dashboard,
        name="dashboard",
    ),

    # Donors
    path(
        "donors/",
        views.donor_list,
        name="donor_list",
    ),
    path(
        "donors/create/",
        views.donor_create,
        name="donor_create",
    ),
    path(
        "donors/<int:donor_id>/edit/",
        views.donor_update,
        name="donor_update",
    ),

    # Blood Units
    path(
        "units/",
        views.unit_list,
        name="unit_list",
    ),
    path(
        "units/create/",
        views.unit_create,
        name="unit_create",
    ),

    # Blood Requests
    path(
        "requests/",
        views.request_list,
        name="request_list",
    ),
    path(
        "requests/create/",
        views.request_create,
        name="request_create",
    ),
    path(
        "requests/<int:request_id>/",
        views.request_detail,
        name="request_detail",
    ),
    path(
        "requests/<int:request_id>/issue/",
        views.issue_blood,
        name="issue_blood",
    ),
path(
    "requests/<int:request_id>/crossmatch/",
    views.crossmatch_create,
    name="crossmatch_create",
),
    # Transfusion
    path(
        "issues/<int:issue_id>/start-transfusion/",
        views.start_transfusion,
        name="start_transfusion",
    ),
    path(
        "transfusions/<int:transfusion_id>/update/",
        views.update_transfusion,
        name="update_transfusion",
    ),

    # Movements
    path(
        "movements/",
        views.movement_list,
        name="movement_list",
    ),

    # Patient
    path(
        "patients/<int:patient_id>/requests/",
        views.patient_requests,
        name="patient_requests",
    ),
]
