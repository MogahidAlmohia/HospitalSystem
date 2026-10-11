from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path("patient/<int:patient_id>/pdf/", views.patient_file_pdf, name="patient_file_pdf"),
    path("", views.reports_dashboard, name="dashboard"),
]
