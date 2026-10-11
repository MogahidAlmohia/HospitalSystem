from django.contrib import admin
from .models import StaffProfile


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = (
        "employee_number",
        "full_name",
        "role",
        "department",
        "phone",
        "is_active",
        "created_at",
    )

    search_fields = (
        "employee_number",
        "full_name",
        "phone",
    )

    list_filter = (
        "role",
        "department",
        "is_active",
    )
