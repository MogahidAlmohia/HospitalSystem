from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("", views.dashboard, name="dashboard"),

    path("users/", views.user_list, name="user_list"),
    path("human-resources/", views.hr_dashboard, name="hr_dashboard"),
    path("users/create/", views.user_create, name="user_create"),
    path("users/<int:user_id>/edit/", views.user_edit, name="user_edit"),
    path("users/<int:user_id>/toggle/", views.user_toggle, name="user_toggle"),
    path(
        "users/<int:user_id>/permissions/",
        views.user_permissions,
        name="user_permissions"
    ),
]
