from django.urls import path

from . import views


app_name = "system_settings"


urlpatterns = [
    path("", views.settings_dashboard, name="dashboard"),
    path("update/", views.update_settings, name="update"),
]
