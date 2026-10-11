from django.conf import settings
from django.db import models


class LaboratoryDevice(models.Model):
    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("MAINTENANCE", "Maintenance"),
        ("OUT_OF_SERVICE", "Out of Service"),
    ]

    name = models.CharField(max_length=200)
    manufacturer = models.CharField(max_length=200, blank=True)
    model = models.CharField(max_length=200, blank=True)
    serial_number = models.CharField(max_length=200, blank=True)
    department = models.ForeignKey(
        "departments.Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="laboratory_devices",
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="ACTIVE",
    )
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.model}".strip(" -")


class LaboratoryReagent(models.Model):
    name = models.CharField(max_length=200)
    manufacturer = models.CharField(max_length=200, blank=True)
    catalog_number = models.CharField(max_length=100, blank=True)
    device = models.ForeignKey(
        LaboratoryDevice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reagents",
    )
    tests = models.ManyToManyField(
        "LaboratoryTest",
        blank=True,
        related_name="reagents",
    )
    unit = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class LaboratoryReagentStock(models.Model):
    reagent = models.ForeignKey(
        LaboratoryReagent,
        on_delete=models.CASCADE,
        related_name="stock_lots",
    )
    lot_number = models.CharField(max_length=100)
    expiry_date = models.DateField()
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    minimum_stock = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    supplier = models.CharField(max_length=200, blank=True)
    purchase_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["expiry_date", "lot_number"]
        unique_together = ["reagent", "lot_number"]

    def __str__(self):
        return f"{self.reagent.name} - LOT {self.lot_number}"


class LaboratoryStockMovement(models.Model):
    MOVEMENT_TYPES = [
        ("IN", "Stock In"),
        ("OUT", "Stock Out"),
        ("RETURN", "Return"),
        ("ADJUSTMENT", "Adjustment"),
    ]

    stock = models.ForeignKey(
        LaboratoryReagentStock,
        on_delete=models.CASCADE,
        related_name="movements",
    )
    movement_type = models.CharField(
        max_length=20,
        choices=MOVEMENT_TYPES,
    )
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    reference = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="laboratory_stock_movements",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.quantity}"
