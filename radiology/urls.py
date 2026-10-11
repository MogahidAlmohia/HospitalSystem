from django.urls import path
from . import views


app_name = "radiology"


urlpatterns = [
    path("", views.dashboard, name="dashboard"),

    path("orders/", views.order_list, name="order_list"),
    path("orders/create/", views.order_create, name="order_create"),
    path(
        "orders/<int:order_id>/",
        views.order_detail,
        name="order_detail"
    ),
    path(
        "orders/<int:order_id>/status/",
        views.order_update_status,
        name="order_update_status"
    ),
    path(
        "orders/<int:order_id>/report/",
        views.report_create,
        name="report_create"
    ),

    path(
        "exam-types/",
        views.exam_type_list,
        name="exam_type_list"
    ),
    path(
        "exam-types/create/",
        views.exam_type_create,
        name="exam_type_create"
    ),

    path(
        "patients/<int:patient_id>/orders/",
        views.patient_orders,
        name="patient_orders"
    ),
]
