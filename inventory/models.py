from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q


class InventoryCategory(models.Model):
    name_ar = models.CharField(
        max_length=200,
        verbose_name="اسم التصنيف",
    )
    name_en = models.CharField(
        max_length=200,
        verbose_name="Category Name",
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Category Code",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="التصنيف الأب",
    )
    description = models.TextField(
        blank=True,
        verbose_name="الوصف",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="نشط",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name_ar"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["name_ar"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.name_ar} - {self.name_en}"


class UnitOfMeasure(models.Model):
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Unit Code",
    )
    name_ar = models.CharField(
        max_length=100,
        verbose_name="اسم الوحدة",
    )
    name_en = models.CharField(
        max_length=100,
        verbose_name="Unit Name",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="نشطة",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name_en}"


class Supplier(models.Model):
    name_ar = models.CharField(
        max_length=200,
        verbose_name="اسم المورد",
    )
    name_en = models.CharField(
        max_length=200,
        verbose_name="Supplier Name",
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Supplier Code",
    )
    phone = models.CharField(
        max_length=50,
        blank=True,
    )
    email = models.EmailField(
        blank=True,
    )
    address = models.TextField(
        blank=True,
    )
    contact_person = models.CharField(
        max_length=200,
        blank=True,
    )
    tax_number = models.CharField(
        max_length=100,
        blank=True,
    )
    notes = models.TextField(
        blank=True,
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="نشط",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name_ar"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["name_ar"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.name_ar} - {self.name_en}"


class InventoryItem(models.Model):
    class ItemType(models.TextChoices):
        MEDICATION = "MEDICATION", "Medication"
        MEDICAL_SUPPLY = "MEDICAL_SUPPLY", "Medical Supply"
        LAB_REAGENT = "LAB_REAGENT", "Laboratory Reagent"
        BLOOD_BANK_SUPPLY = "BLOOD_BANK_SUPPLY", "Blood Bank Supply"
        SURGICAL_SUPPLY = "SURGICAL_SUPPLY", "Surgical Supply"
        RADIOLOGY_SUPPLY = "RADIOLOGY_SUPPLY", "Radiology Supply"
        NURSING_SUPPLY = "NURSING_SUPPLY", "Nursing Supply"
        GENERAL_SUPPLY = "GENERAL_SUPPLY", "General Supply"
        OTHER = "OTHER", "Other"

    code = models.CharField(
        max_length=80,
        unique=True,
        verbose_name="Item Code",
    )
    name_ar = models.CharField(
        max_length=250,
        verbose_name="اسم الصنف",
    )
    name_en = models.CharField(
        max_length=250,
        verbose_name="Item Name",
    )
    category = models.ForeignKey(
        InventoryCategory,
        on_delete=models.PROTECT,
        related_name="items",
        verbose_name="التصنيف",
    )
    unit = models.ForeignKey(
        UnitOfMeasure,
        on_delete=models.PROTECT,
        related_name="items",
        verbose_name="الوحدة",
    )
    item_type = models.CharField(
        max_length=40,
        choices=ItemType.choices,
        default=ItemType.OTHER,
        verbose_name="نوع الصنف",
    )
    description = models.TextField(
        blank=True,
    )
    manufacturer = models.CharField(
        max_length=250,
        blank=True,
    )
    barcode = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        unique=True,
    )
    reorder_level = models.DecimalField(
        max_digits=18,
        decimal_places=3,
        default=Decimal("0"),
        validators=[MinValueValidator(Decimal("0"))],
    )
    maximum_level = models.DecimalField(
        max_digits=18,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0"))],
    )
    requires_batch = models.BooleanField(
        default=False,
    )
    requires_expiry = models.BooleanField(
        default=False,
    )
    is_active = models.BooleanField(
        default=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name_ar"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["name_ar"]),
            models.Index(fields=["name_en"]),
            models.Index(fields=["category"]),
            models.Index(fields=["is_active"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(maximum_level__isnull=True)
                    | Q(maximum_level__gte=models.F("reorder_level"))
                ),
                name="inventory_item_max_gte_reorder",
            ),
        ]

    def __str__(self):
        return f"{self.code} - {self.name_ar}"


class Warehouse(models.Model):
    class WarehouseType(models.TextChoices):
        CENTRAL = "CENTRAL", "Central Warehouse"
        DEPARTMENT = "DEPARTMENT", "Department Warehouse"
        OTHER = "OTHER", "Other"

    name_ar = models.CharField(
        max_length=200,
        verbose_name="اسم المستودع",
    )
    name_en = models.CharField(
        max_length=200,
        verbose_name="Warehouse Name",
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Warehouse Code",
    )
    department = models.ForeignKey(
        "departments.Department",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="inventory_warehouses",
        verbose_name="القسم",
    )
    location = models.CharField(
        max_length=250,
        blank=True,
    )
    warehouse_type = models.CharField(
        max_length=30,
        choices=WarehouseType.choices,
        default=WarehouseType.OTHER,
    )
    is_active = models.BooleanField(
        default=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name_ar"]
        indexes = [
            models.Index(fields=["department"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.name_ar} - {self.code}"


class StorageLocation(models.Model):
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="locations",
        verbose_name="المستودع",
    )
    name_ar = models.CharField(
        max_length=200,
        verbose_name="اسم الموقع",
    )
    name_en = models.CharField(
        max_length=200,
        verbose_name="Location Name",
    )
    code = models.CharField(
        max_length=50,
        verbose_name="Location Code",
    )
    description = models.TextField(
        blank=True,
    )
    is_active = models.BooleanField(
        default=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["warehouse", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["warehouse", "code"],
                name="inventory_location_warehouse_code_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["warehouse"]),
        ]

    def __str__(self):
        return f"{self.warehouse.code} / {self.code} - {self.name_ar}"


class StockBatch(models.Model):
    item = models.ForeignKey(
        InventoryItem,
        on_delete=models.PROTECT,
        related_name="batches",
        verbose_name="الصنف",
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="stock_batches",
        verbose_name="المستودع",
    )
    location = models.ForeignKey(
        StorageLocation,
        on_delete=models.PROTECT,
        related_name="stock_batches",
        verbose_name="موقع التخزين",
    )
    batch_number = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        verbose_name="رقم التشغيلة",
    )
    expiry_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="تاريخ الانتهاء",
    )
    quantity = models.DecimalField(
        max_digits=18,
        decimal_places=3,
        default=Decimal("0"),
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="الكمية",
    )
    unit_cost = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        default=Decimal("0"),
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="تكلفة الوحدة",
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="stock_batches",
        verbose_name="المورد",
    )
    received_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(
        default=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["expiry_date", "id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gte=0),
                name="stock_batch_quantity_gte_zero",
            ),
            models.CheckConstraint(
                condition=Q(unit_cost__gte=0),
                name="stock_batch_unit_cost_gte_zero",
            ),
            models.UniqueConstraint(
                fields=["warehouse", "item", "batch_number"],
                condition=Q(batch_number__isnull=False),
                name="stock_batch_warehouse_item_batch_unique",
            ),
        ]
        indexes = [
            models.Index(fields=["item"]),
            models.Index(fields=["warehouse"]),
            models.Index(fields=["location"]),
            models.Index(fields=["expiry_date"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        batch = self.batch_number or "NO-BATCH"
        return f"{self.item.code} / {batch} / {self.quantity}"


class StockMovement(models.Model):
    class MovementType(models.TextChoices):
        RECEIPT = "RECEIPT", "استلام"
        ISSUE = "ISSUE", "صرف"
        RETURN = "RETURN", "إرجاع"
        TRANSFER_OUT = "TRANSFER_OUT", "تحويل صادر"
        TRANSFER_IN = "TRANSFER_IN", "تحويل وارد"
        ADJUSTMENT = "ADJUSTMENT", "تسوية"
        DISPOSAL = "DISPOSAL", "إتلاف"
        EXPIRY = "EXPIRY", "انتهاء صلاحية"

    batch = models.ForeignKey(
        StockBatch,
        on_delete=models.PROTECT,
        related_name="movements",
        verbose_name="التشغيلة",
    )
    movement_type = models.CharField(
        max_length=30,
        choices=MovementType.choices,
        verbose_name="نوع الحركة",
    )
    quantity = models.DecimalField(
        max_digits=18,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0.001"))],
        verbose_name="الكمية",
    )
    reference_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="نوع المرجع",
    )
    reference_id = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        verbose_name="رقم المرجع",
    )
    reason = models.TextField(
        blank=True,
        verbose_name="السبب",
    )
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="inventory_stock_movements",
        verbose_name="نفذ بواسطة",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gt=0),
                name="stock_movement_quantity_gt_zero",
            ),
        ]
        indexes = [
            models.Index(fields=["batch", "created_at"]),
            models.Index(fields=["movement_type"]),
            models.Index(fields=["reference_type", "reference_id"]),
        ]

    def __str__(self):
        return f"{self.batch} / {self.movement_type} / {self.quantity}"


class StockTransfer(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        REQUESTED = "REQUESTED", "Requested"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        IN_TRANSIT = "IN_TRANSIT", "In Transit"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    source_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="outgoing_transfers",
        verbose_name="المستودع المصدر",
    )
    destination_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="incoming_transfers",
        verbose_name="المستودع المستلم",
    )
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="inventory_requested_transfers",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="inventory_approved_transfers",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.CheckConstraint(
                condition=~Q(
                    source_warehouse=models.F("destination_warehouse")
                ),
                name="stock_transfer_source_ne_destination",
            ),
        ]
        indexes = [
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self):
        return (
            f"Transfer #{self.pk}: "
            f"{self.source_warehouse.code} -> "
            f"{self.destination_warehouse.code}"
        )


class StockTransferItem(models.Model):
    transfer = models.ForeignKey(
        StockTransfer,
        on_delete=models.CASCADE,
        related_name="items",
    )
    item = models.ForeignKey(
        InventoryItem,
        on_delete=models.PROTECT,
        related_name="transfer_items",
    )
    batch = models.ForeignKey(
        StockBatch,
        on_delete=models.PROTECT,
        related_name="transfer_items",
    )
    quantity = models.DecimalField(
        max_digits=18,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0.001"))],
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gt=0),
                name="stock_transfer_item_quantity_gt_zero",
            ),
        ]
        indexes = [
            models.Index(fields=["transfer"]),
            models.Index(fields=["item"]),
            models.Index(fields=["batch"]),
        ]

    def __str__(self):
        return f"{self.item.code} / {self.quantity}"


class StockAdjustment(models.Model):
    batch = models.ForeignKey(
        StockBatch,
        on_delete=models.PROTECT,
        related_name="adjustments",
        verbose_name="التشغيلة",
    )
    old_quantity = models.DecimalField(
        max_digits=18,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0"))],
    )
    new_quantity = models.DecimalField(
        max_digits=18,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0"))],
    )
    difference = models.DecimalField(
        max_digits=18,
        decimal_places=3,
    )
    reason = models.TextField(
        verbose_name="سبب التعديل",
    )
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="inventory_performed_adjustments",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="inventory_approved_adjustments",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["batch", "created_at"]),
        ]

    def __str__(self):
        return f"Adjustment #{self.pk} / {self.batch}"


class Purchase(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "مسودة"
        ORDERED = "ORDERED", "معتمد"
        PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED", "مستلم جزئيًا"
        RECEIVED = "RECEIVED", "مكتمل الاستلام"
        CANCELLED = "CANCELLED", "ملغى"

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name="purchases",
        verbose_name="المورد",
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="purchases",
        verbose_name="المستودع",
    )
    purchase_number = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="رقم الشراء",
    )
    purchase_date = models.DateField(
        verbose_name="تاريخ الشراء",
    )
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    total_amount = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=Decimal("0"),
        validators=[MinValueValidator(Decimal("0"))],
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="inventory_purchases",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-purchase_date", "-id"]
        indexes = [
            models.Index(fields=["supplier"]),
            models.Index(fields=["warehouse"]),
            models.Index(fields=["purchase_date"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(total_amount__gte=0),
                name="purchase_total_amount_gte_zero",
            ),
        ]

    def __str__(self):
        return self.purchase_number


class PurchaseItem(models.Model):
    purchase = models.ForeignKey(
        Purchase,
        on_delete=models.CASCADE,
        related_name="items",
    )
    item = models.ForeignKey(
        InventoryItem,
        on_delete=models.PROTECT,
        related_name="purchase_items",
    )
    batch = models.ForeignKey(
        StockBatch,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="purchase_items",
    )
    quantity = models.DecimalField(
        max_digits=18,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0.001"))],
    )
    received_quantity = models.DecimalField(
        max_digits=18,
        decimal_places=3,
        default=Decimal("0"),
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="الكمية المستلمة",
    )
    unit_cost = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0"))],
    )

    @property
    def remaining_quantity(self):
        return self.quantity - self.received_quantity

    @property
    def total_cost(self):
        return self.quantity * self.unit_cost

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gt=0),
                name="purchase_item_quantity_gt_zero",
            ),
            models.CheckConstraint(
                condition=Q(received_quantity__gte=0),
                name="purchase_item_received_quantity_gte_zero",
            ),
            models.CheckConstraint(
                condition=Q(received_quantity__lte=F("quantity")),
                name="purchase_item_received_quantity_lte_quantity",
            ),
            models.CheckConstraint(
                condition=Q(unit_cost__gte=0),
                name="purchase_item_unit_cost_gte_zero",
            ),
        ]
        indexes = [
            models.Index(fields=["purchase"]),
            models.Index(fields=["item"]),
            models.Index(fields=["batch"]),
        ]

    def __str__(self):
        return f"{self.item.code} / {self.quantity}"


# ============================================================
# IMPORTANT ARCHITECTURAL NOTE
# ============================================================
#
# Laboratory compatibility models remain intentionally outside
# this file:
#
# laboratory.models_inventory.LaboratoryReagent
# laboratory.models_inventory.LaboratoryReagentStock
# laboratory.models_inventory.LaboratoryStockMovement
#
# They are NOT imported here and NOT registered as inventory
# models. They remain the laboratory compatibility layer.
#
# Stock-changing operations for the central inventory will later
# be implemented in inventory/services.py using:
#   transaction.atomic()
#   select_for_update()
#   server-side permission checks
#   immutable StockMovement records
#
# Cross-table/business rules are intentionally NOT enforced
# solely through database CheckConstraints.
#
# Database integrity constraints are maintained in migration
# 0002_inventory_integrity.py.
#
