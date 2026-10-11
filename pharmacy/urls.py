from django.urls import path
from . import views

app_name = "pharmacy"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),

    path("medicines/", views.medicine_list, name="medicine_list"),
    path("medicines/create/", views.medicine_create, name="medicine_create"),
    path(
        "medicines/<int:medicine_id>/edit/",
        views.medicine_update,
        name="medicine_update",
    ),

    path("prescriptions/", views.prescription_list, name="prescription_list"),
    path(
        "prescriptions/create/",
        views.prescription_create,
        name="prescription_create",
    ),
    path(
        "prescriptions/<int:prescription_id>/",
        views.prescription_detail,
        name="prescription_detail",
    ),
    path(
        "prescriptions/<int:prescription_id>/add-item/",
        views.prescription_add_item,
        name="prescription_add_item",
    ),
    path(
        "prescriptions/<int:prescription_id>/dispense/",
        views.prescription_dispense,
        name="prescription_dispense",
    ),

    path("stock/", views.stock_list, name="stock_list"),
    path(
        "stock/movements/",
        views.stock_movements,
        name="stock_movements",
    ),
    path(
        "stock/<int:medicine_id>/receive/",
        views.stock_receive,
        name="stock_receive",
    ),
    path(
        "stock/<int:medicine_id>/adjust/",
        views.stock_adjust,
        name="stock_adjust",
    ),

    path(
        "patients/<int:patient_id>/prescriptions/",
        views.patient_prescriptions,
        name="patient_prescriptions",
    ),
]
