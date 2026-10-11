from django.urls import path

from . import views


app_name = "departments"


urlpatterns = [
    # ========================================================
    # DEPARTMENT CENTER
    # ========================================================

    path(
        "",
        views.department_list,
        name="list",
    ),

    path(
        "create/",
        views.department_create,
        name="create",
    ),

    # ========================================================
    # DEPARTMENT DASHBOARD
    # ========================================================

    path(
        "<int:department_id>/",
        views.department_dashboard,
        name="dashboard",
    ),

    # ========================================================
    # DEPARTMENT OPERATIONS
    # ========================================================

    path(
        "<int:department_id>/patients/",
        views.department_patients,
        name="patients",
    ),

    path(
        "<int:department_id>/visits/",
        views.department_visits,
        name="visits",
    ),

    path(
        "<int:department_id>/lab-orders/",
        views.department_lab_orders,
        name="lab_orders",
    ),

    path(
        "<int:department_id>/results/",
        views.department_results,
        name="results",
    ),

    path(
        "<int:department_id>/required-results/",
        views.department_required_results,
        name="required_results",
    ),

    path(
        "<int:department_id>/achievements/",
        views.department_achievements,
        name="achievements",
    ),

    # ========================================================
    # MANAGEMENT
    # ========================================================

    path(
        "<int:department_id>/edit/",
        views.department_edit,
        name="edit",
    ),

    path(
        "<int:department_id>/toggle/",
        views.department_toggle,
        name="toggle",
    ),
]
