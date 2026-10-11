from django.contrib import admin

from .models import (
    LaboratoryTest,
    LaboratoryOrder,
    LaboratoryOrderItem,
)


@admin.register(LaboratoryTest)
class LaboratoryTestAdmin(admin.ModelAdmin):

    list_display = (
        "code",
        "name_en",
        "name_ar",
        "department",
        "sample_type",
        "unit",
        "reference_range",
        "price",
        "is_active",
    )

    list_filter = (
        "department",
        "sample_type",
        "is_active",
    )

    search_fields = (
        "code",
        "name_en",
        "name_ar",
        "department__name_en",
        "department__name_ar",
    )

    ordering = (
        "department__name_en",
        "name_en",
    )

    list_per_page = 50


@admin.register(LaboratoryOrder)
class LaboratoryOrderAdmin(admin.ModelAdmin):

    list_display = (
        "order_number",
        "patient",
        "visit",
        "requesting_department",
        "requesting_doctor",
        "priority",
        "status",
        "requested_at",
    )

    list_filter = (
        "status",
        "priority",
        "requesting_department",
    )

    search_fields = (
        "order_number",
        "patient__full_name",
        "patient__patient_number",
    )

    autocomplete_fields = (
        "patient",
        "requesting_department",
    )

    date_hierarchy = "requested_at"

    ordering = (
        "-requested_at",
    )


@admin.register(LaboratoryOrderItem)
class LaboratoryOrderItemAdmin(admin.ModelAdmin):

    list_display = (
        "order",
        "test",
        "status",
        "sample_id",
        "result",
        "result_numeric",
        "result_flag",
        "verified",
        "updated_at",
    )

    list_filter = (
        "status",
        "verified",
        "test__department",
    )

    search_fields = (
        "order__order_number",
        "order__patient__full_name",
        "test__code",
        "test__name_en",
        "test__name_ar",
        "sample_id",
        "result",
    )

    autocomplete_fields = (
        "order",
        "test",
    )

    ordering = (
        "-updated_at",
    )

    list_per_page = 50
