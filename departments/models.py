from django.db import models


class Department(models.Model):
    DEPARTMENT_TYPES = [
        ("CLINICAL", "Clinical"),
        ("DIAGNOSTIC", "Diagnostic"),
        ("ADMIN", "Administrative"),
        ("SUPPORT", "Support"),
    ]

    name_ar = models.CharField(
        max_length=200,
        verbose_name="اسم القسم"
    )

    name_en = models.CharField(
        max_length=200,
        verbose_name="Department Name"
    )

    code = models.CharField(
        max_length=30,
        unique=True,
        verbose_name="Department Code"
    )

    department_type = models.CharField(
        max_length=20,
        choices=DEPARTMENT_TYPES,
        default="CLINICAL"
    )

    phone = models.CharField(
        max_length=30,
        blank=True
    )

    location = models.CharField(
        max_length=200,
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.name_ar} - {self.name_en}"

    class Meta:
        ordering = ["name_ar"]
