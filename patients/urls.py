from django.urls import path
from . import views

app_name = "patients"

urlpatterns = [
    path("", views.patient_list, name="list"),
    path("create/", views.patient_create, name="create"),
    path("search/", views.patient_search, name="search"),
    path("<int:patient_id>/", views.patient_detail, name="detail"),
    path("<int:patient_id>/edit/", views.patient_edit, name="edit"),
    path("<int:patient_id>/visits/", views.patient_visits, name="visits"),
    path("<int:patient_id>/visits/create/", views.visit_create, name="visit_create"),
    path("visits/<int:visit_id>/", views.visit_detail, name="visit_detail"),
    path("visits/<int:visit_id>/diagnosis/create/", views.diagnosis_create, name="diagnosis_create"),
]
