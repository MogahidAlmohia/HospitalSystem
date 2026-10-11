from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Bill(models.Model):
    STATUS_CHOICES = [
        ("DRAFT", "مسودة"),
        ("ISSUED", "صادرة"),
        ("PARTIAL", "مدفوعة جزئياً"),
        ("PAID", "مدفوعة"),
        ("CANCELLED", "ملغاة"),
    ]

    PAYMENT_METHOD_CHOICES = [
        ("CASH", "نقداً"),
        ("TRANSFER", "تحويل"),
        ("OTHER", "أخرى"),
    ]

    bill_number = models.CharField(
        "رقم الفاتورة",
        max_length=30,
        unique=True,
        editable=False,
    )

    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.PROTECT,
        related_name="bills",
        verbose_name="المريض",
    )

    visit = models.ForeignKey(
        "patients.Visit",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bills",
        verbose_name="الزيارة",
    )

    status = models.CharField(
        "الحالة",
        max_length=20,
        choices=STATUS_CHOICES,
        default="DRAFT",
    )

    payment_method = models.CharField(
        "طريقة الدفع",
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default="CASH",
    )

    subtotal = models.DecimalField(
        "الإجمالي قبل الخصم",
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    discount = models.DecimalField(
        "الخصم",
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    total = models.DecimalField(
        "الإجمالي النهائي",
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    paid_amount = models.DecimalField(
        "المدفوع",
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    notes = models.TextField(
        "ملاحظات",
        blank=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_bills",
        verbose_name="أنشأها",
    )

    created_at = models.DateTimeField(
        "تاريخ الإنشاء",
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        "آخر تحديث",
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["patient"]),
            models.Index(fields=["visit"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]
        verbose_name = "فاتورة"
        verbose_name_plural = "الفواتير"

    def __str__(self):
        return f"{self.bill_number} - {self.patient.full_name}"

    @property
    def remaining_amount(self):
        return max(self.total - self.paid_amount, Decimal("0.00"))

    def calculate_totals(self):
        items_total = sum(
            (item.line_total for item in self.items.all()),
            Decimal("0.00"),
        )

        self.subtotal = items_total
        self.total = max(
            self.subtotal - self.discount,
            Decimal("0.00"),
        )

        if self.paid_amount > self.total:
            self.paid_amount = self.total

        if self.total == Decimal("0.00"):
            self.status = "DRAFT"
        elif self.paid_amount == Decimal("0.00"):
            if self.status == "PAID":
                self.status = "ISSUED"
        elif self.paid_amount < self.total:
            self.status = "PARTIAL"
        else:
            self.paid_amount = self.total
            self.status = "PAID"

    def save(self, *args, **kwargs):
        if not self.bill_number:
            today = timezone.localdate()
            prefix = f"INV-{today:%Y%m%d}-"

            last_bill = (
                Bill.objects
                .filter(bill_number__startswith=prefix)
                .order_by("-id")
                .first()
            )

            if last_bill:
                try:
                    last_number = int(last_bill.bill_number.split("-")[-1])
                except (ValueError, IndexError):
                    last_number = 0
            else:
                last_number = 0

            self.bill_number = f"{prefix}{last_number + 1:04d}"

        super().save(*args, **kwargs)


class BillItem(models.Model):
    SERVICE_TYPE_CHOICES = [
        ("LABORATORY", "مختبر"),
        ("RADIOLOGY", "أشعة"),
        ("PHARMACY", "صيدلية"),
        ("SURGERY", "عمليات"),
        ("INPATIENT", "تنويم"),
        ("EMERGENCY", "طوارئ"),
        ("CONSULTATION", "معاينة"),
        ("PROCEDURE", "إجراء طبي"),
        ("OTHER", "أخرى"),
    ]

    bill = models.ForeignKey(
        Bill,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="الفاتورة",
    )

    service_type = models.CharField(
        "نوع الخدمة",
        max_length=30,
        choices=SERVICE_TYPE_CHOICES,
    )

    description = models.CharField(
        "وصف الخدمة",
        max_length=255,
    )

    quantity = models.DecimalField(
        "الكمية",
        max_digits=10,
        decimal_places=2,
        default=Decimal("1.00"),
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    unit_price = models.DecimalField(
        "سعر الوحدة",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    line_total = models.DecimalField(
        "الإجمالي",
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    notes = models.CharField(
        "ملاحظات",
        max_length=255,
        blank=True,
    )

    created_at = models.DateTimeField(
        "تاريخ الإضافة",
        auto_now_add=True,
    )

    class Meta:
        ordering = ["id"]
        indexes = [
            models.Index(fields=["bill"]),
            models.Index(fields=["service_type"]),
        ]
        verbose_name = "بند فاتورة"
        verbose_name_plural = "بنود الفواتير"

    def __str__(self):
        return f"{self.description} - {self.line_total}"

    def calculate_total(self):
        self.line_total = self.quantity * self.unit_price

    def save(self, *args, **kwargs):
        self.calculate_total()
        super().save(*args, **kwargs)


class BillPayment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ("CASH", "نقداً"),
        ("TRANSFER", "تحويل"),
        ("OTHER", "أخرى"),
    ]

    bill = models.ForeignKey(
        Bill,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="الفاتورة",
    )

    amount = models.DecimalField(
        "المبلغ",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    payment_method = models.CharField(
        "طريقة الدفع",
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default="CASH",
    )

    reference = models.CharField(
        "مرجع العملية",
        max_length=100,
        blank=True,
    )

    notes = models.CharField(
        "ملاحظات",
        max_length=255,
        blank=True,
    )

    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="received_bill_payments",
        verbose_name="استلمها",
    )

    paid_at = models.DateTimeField(
        "تاريخ الدفع",
        default=timezone.now,
    )

    class Meta:
        ordering = ["-paid_at"]
        indexes = [
            models.Index(fields=["bill"]),
            models.Index(fields=["paid_at"]),
        ]
        verbose_name = "دفعة"
        verbose_name_plural = "الدفعات"

    def __str__(self):
        return f"{self.bill.bill_number} - {self.amount}"
