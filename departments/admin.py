from django.contrib import admin
from .models import Department


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = (
        "name_ar",
        "name_en",
        "code",
        "department_type",
        "phone",
        "is_active",
    )

    search_fields = (
        "name_ar",
        "name_en",
        "code",
    )

    list_filter = (
        "department_type",
        "is_active",
    )
