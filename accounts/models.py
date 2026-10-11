from django.db import models
from django.contrib.auth.models import User
from departments.models import Department


class StaffProfile(models.Model):
    ROLE_CHOICES = [
        ("ADMIN", "System Administrator"),
        ("MANAGER", "Hospital Manager"),
        ("RECEPTION", "Reception"),
        ("DOCTOR", "Doctor"),
        ("LAB", "Laboratory"),
        ("RADIOLOGY", "Radiology"),
        ("PHARMACY", "Pharmacy"),
        ("NURSING", "Nursing"),
        ("EMERGENCY", "Emergency"),
        ("INPATIENT", "Inpatient"),
        ("SURGERY", "Surgery"),
        ("BLOOD_BANK", "Blood Bank"),
        ("BILLING", "Billing"),
        ("INVENTORY", "Inventory"),
        ("OTHER", "Other"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="staff_profile"
    )

    employee_number = models.CharField(
        max_length=50,
        unique=True
    )

    full_name = models.CharField(
        max_length=200
    )

    role = models.CharField(
        max_length=30,
        choices=ROLE_CHOICES
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staff"
    )

    phone = models.CharField(
        max_length=30,
        blank=True
    )

    # صلاحيات إضافية خاصة بهذا المستخدم
    # تبقى صلاحيات الوظيفة الأساسية ROLE_PERMISSIONS فعالة.
    custom_permissions = models.JSONField(
        default=list,
        blank=True
    )

    # صلاحيات ممنوعة لهذا المستخدم
    # لها أولوية على صلاحيات الدور والصلاحيات الإضافية.
    denied_permissions = models.JSONField(
        default=list,
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
        return f"{self.employee_number} - {self.full_name}"
