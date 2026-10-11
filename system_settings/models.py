from django.db import models


class SystemSetting(models.Model):
    """
    إعداد مركزي للنظام.

    يتم تخزين إعدادات النظام في قاعدة البيانات حتى يستطيع
    المسؤول تعديلها من واجهة النظام دون تعديل config/settings.py.
    """

    CATEGORY_CHOICES = [
        ("HOSPITAL", "Hospital"),
        ("NUMBERING", "Numbering"),
        ("CENTERS", "Centers"),
        ("LABORATORY", "Laboratory"),
        ("REPORTS", "Reports"),
        ("NOTIFICATIONS", "Notifications"),
        ("BILLING", "Billing"),
        ("LOCALIZATION", "Localization"),
        ("SECURITY", "Security"),
        ("BACKUP", "Backup"),
        ("MAINTENANCE", "Maintenance"),
    ]

    key = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Setting Key",
    )

    value = models.TextField(
        blank=True,
        default="",
        verbose_name="Setting Value",
    )

    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        default="HOSPITAL",
        db_index=True,
        verbose_name="Category",
    )

    description = models.CharField(
        max_length=500,
        blank=True,
        default="",
        verbose_name="Description",
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Active",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["category", "key"]
        verbose_name = "System Setting"
        verbose_name_plural = "System Settings"

    def __str__(self):
        return f"{self.key} = {self.value}"
