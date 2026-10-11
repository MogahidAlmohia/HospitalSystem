from django.urls import path
from . import views

app_name = "laboratory"

urlpatterns = [
    path(
        "result-workflow/",
        views.result_workflow_dashboard,
        name="result_workflow_dashboard",
    ),

    path("report-settings/", views.report_settings, name="report_settings"),
    path("tests/", views.test_list, name="test_list"),
    path("tests/create/", views.test_create, name="test_create"),
    path("tests/<int:test_id>/edit/", views.test_edit, name="test_edit"),
    path("tests/<int:test_id>/toggle/", views.test_toggle, name="test_toggle"),
    path("tests/<int:test_id>/delete/", views.test_delete, name="test_delete"),

    path("sample-reception/", views.sample_reception, name="sample_reception"),

    path(
        "",
        views.laboratory_dashboard,
        name="dashboard"
    ),

    path(
        "orders/<int:order_id>/",
        views.laboratory_order_detail,
        name="order_detail"
    ),

    path(
        "orders/create/<int:visit_id>/",
        views.create_laboratory_order,
        name="create_order"
    ),
    path(
        "orders/create-admission/<int:admission_id>/",
        views.create_laboratory_order,
        name="create_order_for_admission"
    ),

    path(
        "orders/<int:order_id>/results/",
        views.enter_results,
        name="enter_results"
    ),

    path(
        "orders/<int:order_id>/verify/",
        views.verify_results,
        name="verify_results"
    ),

    path(
        "orders/<int:order_id>/report/",
        views.laboratory_report,
        name="laboratory_report"
    ),

    path(
        "orders/<int:order_id>/report/pdf/",
        views.laboratory_report_pdf,
        name="laboratory_report_pdf"
      ),
      path(
          "orders/<int:order_id>/send-result/",
          views.send_result,
          name="send_result"
      ),

]

urlpatterns += [
    path(
        "audit/",
        views.laboratory_audit_dashboard,
        name="audit_dashboard",
    ),
    path(
        "audit/<int:log_id>/",
        views.laboratory_audit_detail,
        name="audit_detail",
    ),
    path("devices/", views.device_list, name="device_list"),
    path("devices/create/", views.device_create, name="device_create"),
    path("devices/<int:device_id>/edit/", views.device_edit, name="device_edit"),
    path("devices/<int:device_id>/toggle/", views.device_toggle, name="device_toggle"),

    path("reagents/", views.reagent_list, name="reagent_list"),
    path("reagents/create/", views.reagent_create, name="reagent_create"),
    path("reagents/<int:reagent_id>/edit/", views.reagent_edit, name="reagent_edit"),
    path("reagents/<int:reagent_id>/toggle/", views.reagent_toggle, name="reagent_toggle"),

    path("inventory/", views.inventory_dashboard, name="inventory_dashboard"),
    path("inventory/create/", views.stock_create, name="stock_create"),
    path("inventory/<int:stock_id>/movement/", views.stock_movement, name="stock_movement"),
    path(
        "result-deliveries/",
        views.result_delivery_dashboard,
        name="result_delivery_dashboard",
    ),
    path(
        "result-deliveries/<int:delivery_id>/receive/",
        views.receive_result,
        name="receive_result"
    ),
]
