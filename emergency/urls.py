from django.urls import path

from . import views

app_name = "emergency"

urlpatterns = [
    path(
        "",
        views.emergency_dashboard,
        name="dashboard",
    ),
    path(
        "create/",
        views.emergency_case_create,
        name="create",
    ),
    path(
        "search/",
        views.emergency_search,
        name="search",
    ),
    path(
        "<int:case_id>/",
        views.emergency_case_detail,
        name="detail",
    ),
    path(
        "<int:case_id>/edit/",
        views.emergency_case_update,
        name="edit",
    ),
]
