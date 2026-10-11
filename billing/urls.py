from django.urls import path

from . import views


app_name = "billing"


urlpatterns = [
    path(
        "",
        views.dashboard,
        name="dashboard",
    ),

    path(
        "bills/",
        views.bill_list,
        name="bill_list",
    ),

    path(
        "bills/create/",
        views.bill_create,
        name="bill_create",
    ),

    path(
        "bills/<int:bill_id>/",
        views.bill_detail,
        name="bill_detail",
    ),

    path(
        "bills/<int:bill_id>/edit/",
        views.bill_update,
        name="bill_update",
    ),

    path(
        "bills/<int:bill_id>/items/create/",
        views.bill_item_create,
        name="bill_item_create",
    ),

    path(
        "items/<int:item_id>/delete/",
        views.bill_item_delete,
        name="bill_item_delete",
    ),

    path(
        "bills/<int:bill_id>/payments/create/",
        views.bill_payment_create,
        name="bill_payment_create",
    ),

    path(
        "bills/<int:bill_id>/status/<str:status>/",
        views.bill_status_update,
        name="bill_status_update",
    ),

    path(
        "patients/<int:patient_id>/",
        views.patient_bills,
        name="patient_bills",
    ),
]
