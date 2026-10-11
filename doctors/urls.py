from django.urls import path
from . import views


app_name = "doctors"


urlpatterns = [
    path("", views.doctor_list, name="list"),
    path("create/", views.doctor_create, name="create"),
    path("<int:doctor_id>/edit/", views.doctor_edit, name="edit"),
    path("<int:doctor_id>/toggle/", views.doctor_toggle, name="toggle"),
]
