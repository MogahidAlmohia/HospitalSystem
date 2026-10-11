from django.urls import path

from . import views


app_name = "surgery"


urlpatterns = [
    path("", views.dashboard, name="dashboard"),

    path(
        "orders/",
        views.order_list,
        name="order_list",
    ),

    path(
        "orders/create/",
        views.order_create,
        name="order_create",
    ),

    path(
        "orders/<int:order_id>/",
        views.order_detail,
        name="order_detail",
    ),

    path(
        "orders/<int:order_id>/edit/",
        views.order_update,
        name="order_update",
    ),

    path(
        "orders/<int:order_id>/status/<str:status>/",
        views.order_status_update,
        name="order_status_update",
    ),

    path(
        "orders/<int:order_id>/procedures/create/",
        views.procedure_create,
        name="procedure_create",
    ),

    path(
        "orders/<int:order_id>/team/create/",
        views.team_member_create,
        name="team_member_create",
    ),

    path(
        "orders/<int:order_id>/postoperative-notes/create/",
        views.postoperative_note_create,
        name="postoperative_note_create",
    ),

    path(
        "types/",
        views.surgery_type_list,
        name="type_list",
    ),

    path(
        "types/create/",
        views.surgery_type_create,
        name="type_create",
    ),

    path(
        "types/<int:type_id>/edit/",
        views.surgery_type_update,
        name="type_update",
    ),

    path(
        "patients/<int:patient_id>/",
        views.patient_surgeries,
        name="patient_surgeries",
    ),
]
