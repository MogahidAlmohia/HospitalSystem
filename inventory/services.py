from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import (
    InventoryItem,
    Supplier,
    StockBatch,
    StockMovement,
    StockTransfer,
    StockTransferItem,
    StockAdjustment,
    Warehouse,
    StorageLocation,
    Purchase,
    PurchaseItem,
)


# ============================================================
# PHASE 13.4.3.8.1
# CENTRAL INVENTORY SERVICE LAYER
#
# IMPORTANT:
# - No view should modify stock quantity directly.
# - Every stock mutation must pass through this service layer.
# - Every stock mutation must create an audit movement.
# - Transactions are atomic.
# - Stock rows are locked before mutation.
# ============================================================


class InventoryServiceError(ValidationError):
    """
    Base exception for inventory business-rule violations.
    """
    pass


class InventoryPermissionError(InventoryServiceError):
    """
    Raised when the actor is not allowed to perform an operation.
    """
    pass


class InventoryStockError(InventoryServiceError):
    """
    Raised for stock availability/integrity violations.
    """
    pass


# ============================================================
# COMMON VALIDATION HELPERS
# ============================================================

def _require_authenticated_user(user):
    if user is None or not getattr(user, "is_authenticated", False):
        raise InventoryPermissionError(
            "يجب تسجيل الدخول لتنفيذ عملية المخزون."
        )


def _decimal_quantity(value) -> Decimal:
    try:
        quantity = Decimal(str(value))
    except Exception:
        raise InventoryStockError(
            "الكمية غير صالحة."
        )

    if quantity <= 0:
        raise InventoryStockError(
            "يجب أن تكون الكمية أكبر من صفر."
        )

    return quantity


def _get_locked_batch(batch_id):
    return (
        StockBatch.objects
        .select_for_update()
        .select_related(
            "item",
            "warehouse",
            "location",
            "supplier",
        )
        .get(pk=batch_id)
    )


def _validate_batch_location(batch):
    if batch.location.warehouse_id != batch.warehouse_id:
        raise InventoryStockError(
            "موقع التخزين لا يتبع المستودع المحدد للدفعة."
        )


def _validate_item_for_stock(item: InventoryItem):
    if not item.is_active:
        raise InventoryStockError(
            "لا يمكن تنفيذ حركة مخزون لصنف غير نشط."
        )


def _validate_batch_for_issue(batch):
    _validate_item_for_stock(batch.item)
    _validate_batch_location(batch)

    if not batch.is_active:
        raise InventoryStockError(
            "دفعة المخزون غير نشطة."
        )

    if batch.expiry_date and batch.expiry_date < date.today():
        raise InventoryStockError(
            "لا يمكن صرف دفعة منتهية الصلاحية."
        )


def _validate_batch_requirements(
    item: InventoryItem,
    batch_number=None,
    expiry_date=None,
):
    normalized_batch = (
        str(batch_number).strip()
        if batch_number is not None
        and str(batch_number).strip()
        else None
    )

    if item.requires_batch and not normalized_batch:
        raise InventoryStockError(
            "هذا الصنف يتطلب رقم Batch."
        )

    if item.requires_expiry and expiry_date is None:
        raise InventoryStockError(
            "هذا الصنف يتطلب تاريخ انتهاء."
        )

    return normalized_batch


def _validate_warehouse_location(
    warehouse: Warehouse,
    location: StorageLocation,
):
    if location.warehouse_id != warehouse.id:
        raise InventoryStockError(
            "موقع التخزين لا يتبع المستودع المحدد."
        )

    if not warehouse.is_active:
        raise InventoryStockError(
            "المستودع غير نشط."
        )

    if not location.is_active:
        raise InventoryStockError(
            "موقع التخزين غير نشط."
        )


def _create_movement(
    *,
    batch,
    movement_type,
    quantity,
    performed_by,
    reference_type="MANUAL",
    reference_id=None,
    reason="",
):
    quantity = _decimal_quantity(quantity)
    _require_authenticated_user(performed_by)

    return StockMovement.objects.create(
        batch=batch,
        movement_type=movement_type,
        quantity=quantity,
        reference_type=reference_type,
        reference_id=reference_id,
        reason=reason or "Inventory service operation",
        performed_by=performed_by,
    )


# ============================================================
# RECEIPT
# ============================================================

@transaction.atomic
def receive_stock(
    *,
    item_id,
    warehouse_id,
    location_id,
    quantity,
    performed_by,
    batch_number=None,
    expiry_date=None,
    unit_cost=Decimal("0"),
    supplier_id=None,
    reference_type="MANUAL",
    reference_id=None,
    reason="",
):
    """
    Receive stock into a warehouse/location.

    Creates or updates a compatible StockBatch and creates
    a RECEIPT StockMovement.

    Business rules:
    - quantity must be positive
    - inactive items cannot receive stock
    - batch/expiry requirements are enforced
    - warehouse/location relationship is enforced
    - supplier is stored on the StockBatch when supplied
    - newly created stock starts with the received quantity
    - existing batch quantity is incremented atomically
    - a RECEIPT movement is always created
    """

    _require_authenticated_user(performed_by)

    quantity = _decimal_quantity(quantity)

    item = InventoryItem.objects.get(pk=item_id)
    warehouse = Warehouse.objects.get(pk=warehouse_id)
    location = StorageLocation.objects.get(pk=location_id)

    _validate_item_for_stock(item)
    _validate_warehouse_location(warehouse, location)

    batch_number = _validate_batch_requirements(
        item,
        batch_number=batch_number,
        expiry_date=expiry_date,
    )

    unit_cost = Decimal(str(unit_cost))

    if unit_cost < 0:
        raise InventoryStockError(
            "تكلفة الوحدة لا يمكن أن تكون سالبة."
        )

    supplier = None

    if supplier_id is not None:
        supplier = Supplier.objects.get(pk=supplier_id)

        if not supplier.is_active:
            raise InventoryStockError(
                "لا يمكن استقبال المخزون من مورد غير نشط."
            )

    # The StockBatch uniqueness rule is:
    # warehouse + item + batch_number
    #
    # Therefore lookup must NOT include location.
    # If the same batch already exists in this warehouse,
    # it must belong to the same storage location.
    batch = (
        StockBatch.objects
        .select_for_update()
        .filter(
            item=item,
            warehouse=warehouse,
            batch_number=batch_number,
        )
        .first()
    )

    if batch is None:

        batch = StockBatch.objects.create(
            item=item,
            warehouse=warehouse,
            location=location,
            batch_number=batch_number,
            expiry_date=expiry_date,
            quantity=quantity,
            unit_cost=unit_cost,
            supplier=supplier,
            received_at=timezone.now(),
            is_active=True,
        )

    else:

        if batch.location_id != location.id:
            raise InventoryStockError(
                "لا يمكن استقبال نفس التشغيلة في موقع تخزين مختلف "
                "داخل المستودع نفسه."
            )

        if (
            item.requires_expiry
            and batch.expiry_date != expiry_date
        ):
            raise InventoryStockError(
                "تاريخ انتهاء الدفعة لا يطابق الدفعة الموجودة."
            )

        if batch.expiry_date and batch.expiry_date < date.today():
            raise InventoryStockError(
                "لا يمكن استقبال كمية جديدة في دفعة منتهية."
            )

        batch.unit_cost = unit_cost
        batch.quantity = batch.quantity + quantity

        if supplier is not None:
            batch.supplier = supplier

        batch.received_at = timezone.now()
        batch.is_active = True

        update_fields = [
            "unit_cost",
            "quantity",
            "received_at",
            "is_active",
            "updated_at",
        ]

        if supplier is not None:
            update_fields.append("supplier")

        batch.save(update_fields=update_fields)

    _validate_batch_location(batch)

    movement = _create_movement(
        batch=batch,
        movement_type="RECEIPT",
        quantity=quantity,
        performed_by=performed_by,
        reference_type=reference_type,
        reference_id=reference_id,
        reason=reason or "Stock receipt",
    )

    return batch, movement



# ============================================================
# ISSUE
# ============================================================

@transaction.atomic
def issue_stock(
    *,
    batch_id,
    quantity,
    performed_by,
    reference_type="MANUAL",
    reference_id=None,
    reason="",
):
    """
    Issue stock from one locked batch.

    Prevents:
    - inactive item
    - inactive batch
    - expired batch
    - negative stock
    - quantity greater than available
    """

    _require_authenticated_user(performed_by)

    quantity = _decimal_quantity(quantity)

    batch = _get_locked_batch(batch_id)

    _validate_batch_for_issue(batch)

    if batch.quantity < quantity:
        raise InventoryStockError(
            "الكمية المطلوبة أكبر من الكمية المتاحة."
        )

    old_quantity = batch.quantity
    new_quantity = old_quantity - quantity

    if new_quantity < 0:
        raise InventoryStockError(
            "لا يمكن أن يصبح المخزون سالبًا."
        )

    batch.quantity = new_quantity
    batch.save(
        update_fields=[
            "quantity",
            "updated_at",
        ]
    )

    movement = _create_movement(
        batch=batch,
        movement_type="ISSUE",
        quantity=quantity,
        performed_by=performed_by,
        reference_type=reference_type,
        reference_id=reference_id,
        reason=reason or "Stock issue",
    )

    return batch, movement


# ============================================================
# RETURN
# ============================================================

@transaction.atomic
def return_stock(
    *,
    batch_id,
    quantity,
    performed_by,
    reference_type="MANUAL",
    reference_id=None,
    reason="",
):
    """
    Return stock to an existing batch.
    """

    _require_authenticated_user(performed_by)

    quantity = _decimal_quantity(quantity)

    batch = _get_locked_batch(batch_id)

    _validate_item_for_stock(batch.item)
    _validate_batch_location(batch)

    if not batch.is_active:
        raise InventoryStockError(
            "لا يمكن الإرجاع إلى دفعة غير نشطة."
        )

    batch.quantity = batch.quantity + quantity
    batch.save(
        update_fields=[
            "quantity",
            "updated_at",
        ]
    )

    movement = _create_movement(
        batch=batch,
        movement_type="RETURN",
        quantity=quantity,
        performed_by=performed_by,
        reference_type=reference_type,
        reference_id=reference_id,
        reason=reason or "Stock return",
    )

    return batch, movement


# ============================================================
# ADJUSTMENT
# ============================================================

@transaction.atomic
def adjust_stock(
    *,
    batch_id,
    new_quantity,
    performed_by,
    reason,
    approved_by=None,
):
    """
    Auditable stock adjustment.

    The caller supplies the desired new quantity.
    Difference is calculated by the service.

    Direct silent quantity overwrite is not allowed.
    """

    _require_authenticated_user(performed_by)

    if not reason or not str(reason).strip():
        raise InventoryStockError(
            "سبب تعديل المخزون مطلوب."
        )

    try:
        new_quantity = Decimal(str(new_quantity))
    except Exception:
        raise InventoryStockError(
            "الكمية الجديدة غير صالحة."
        )

    if new_quantity < 0:
        raise InventoryStockError(
            "الكمية الجديدة لا يمكن أن تكون سالبة."
        )

    batch = _get_locked_batch(batch_id)

    _validate_item_for_stock(batch.item)
    _validate_batch_location(batch)

    old_quantity = batch.quantity
    difference = new_quantity - old_quantity

    if difference == 0:
        raise InventoryStockError(
            "لا يوجد فرق يستدعي تعديل المخزون."
        )

    batch.quantity = new_quantity
    batch.save(
        update_fields=[
            "quantity",
            "updated_at",
        ]
    )

    adjustment = StockAdjustment.objects.create(
        batch=batch,
        old_quantity=old_quantity,
        new_quantity=new_quantity,
        difference=difference,
        reason=str(reason).strip(),
        performed_by=performed_by,
        approved_by=approved_by,
    )

    movement = _create_movement(
        batch=batch,
        movement_type="ADJUSTMENT",
        quantity=abs(difference),
        performed_by=performed_by,
        reference_type="ADJUSTMENT",
        reference_id=adjustment.id,
        reason=str(reason).strip(),
    )

    return batch, adjustment, movement


# ============================================================
# TRANSFER CREATION
# ============================================================

@transaction.atomic
def create_transfer(
    *,
    source_warehouse_id,
    destination_warehouse_id,
    batch_id,
    quantity,
    requested_by,
):
    """
    Creates a transfer request.

    Stock is NOT moved yet.
    Actual stock mutation happens during completion.
    """

    _require_authenticated_user(requested_by)

    quantity = _decimal_quantity(quantity)

    if source_warehouse_id == destination_warehouse_id:
        raise InventoryStockError(
            "لا يمكن التحويل من المستودع إلى نفسه."
        )

    source = Warehouse.objects.get(pk=source_warehouse_id)
    destination = Warehouse.objects.get(
        pk=destination_warehouse_id
    )

    if not source.is_active:
        raise InventoryStockError(
            "المستودع المصدر غير نشط."
        )

    if not destination.is_active:
        raise InventoryStockError(
            "المستودع الوجهة غير نشط."
        )

    batch = _get_locked_batch(batch_id)

    _validate_batch_for_issue(batch)

    if batch.warehouse_id != source.id:
        raise InventoryStockError(
            "دفعة المخزون لا تتبع المستودع المصدر."
        )

    if batch.quantity < quantity:
        raise InventoryStockError(
            "الكمية المطلوبة للتحويل أكبر من المتاح."
        )

    transfer = StockTransfer.objects.create(
        source_warehouse=source,
        destination_warehouse=destination,
        status="REQUESTED",
        requested_by=requested_by,
    )

    StockTransferItem.objects.create(
        transfer=transfer,
        item=batch.item,
        batch=batch,
        quantity=quantity,
    )

    return transfer


# ============================================================
# APPROVE TRANSFER
# ============================================================

@transaction.atomic
def approve_transfer(
    *,
    transfer_id,
    approved_by,
):
    """
    Approves a requested transfer.
    Does not move stock yet.
    """

    _require_authenticated_user(approved_by)

    transfer = (
        StockTransfer.objects
        .select_for_update()
        .get(pk=transfer_id)
    )

    if transfer.status != "REQUESTED":
        raise InventoryStockError(
            "لا يمكن اعتماد التحويل في حالته الحالية."
        )

    transfer.status = "APPROVED"
    transfer.approved_by = approved_by
    transfer.save(
        update_fields=[
            "status",
            "approved_by",
        ]
    )

    return transfer


# ============================================================
# COMPLETE TRANSFER
# ============================================================

@transaction.atomic
def complete_transfer(
    *,
    transfer_id,
    performed_by,
):
    """
    Completes an approved transfer.

    For every transfer item:
    1. Lock source batch.
    2. Verify source warehouse.
    3. Verify sufficient stock.
    4. Decrease source batch.
    5. Create destination batch.
    6. Increase destination stock.
    7. Create TRANSFER_OUT movement.
    8. Create TRANSFER_IN movement.

    All operations are atomic.
    """

    _require_authenticated_user(performed_by)

    transfer = (
        StockTransfer.objects
        .select_for_update()
        .select_related(
            "source_warehouse",
            "destination_warehouse",
        )
        .get(pk=transfer_id)
    )

    if transfer.status != "APPROVED":
        raise InventoryStockError(
            "لا يمكن إكمال تحويل غير معتمد."
        )

    if (
        transfer.source_warehouse_id
        == transfer.destination_warehouse_id
    ):
        raise InventoryStockError(
            "المصدر والوجهة لا يمكن أن يكونا نفس المستودع."
        )

    items = list(
        transfer.items
        .select_related(
            "item",
            "batch",
        )
        .all()
    )

    if not items:
        raise InventoryStockError(
            "التحويل لا يحتوي على أصناف."
        )

    for transfer_item in items:
        source_batch = _get_locked_batch(
            transfer_item.batch_id
        )

        _validate_batch_for_issue(source_batch)

        if (
            source_batch.warehouse_id
            != transfer.source_warehouse_id
        ):
            raise InventoryStockError(
                "دفعة التحويل لا تتبع المستودع المصدر."
            )

        quantity = _decimal_quantity(
            transfer_item.quantity
        )

        if source_batch.quantity < quantity:
            raise InventoryStockError(
                "الكمية المتاحة غير كافية لإكمال التحويل."
            )

        source_batch.quantity -= quantity
        source_batch.save(
            update_fields=[
                "quantity",
                "updated_at",
            ]
        )

        destination_location = (
            StorageLocation.objects
            .filter(
                warehouse_id=transfer.destination_warehouse_id,
                is_active=True,
            )
            .order_by("id")
            .first()
        )

        if destination_location is None:
            raise InventoryStockError(
                "لا يوجد موقع تخزين نشط في المستودع الوجهة."
            )

        destination_batch = (
            StockBatch.objects
            .select_for_update()
            .filter(
                item=source_batch.item,
                warehouse_id=transfer.destination_warehouse_id,
                location=destination_location,
                batch_number=source_batch.batch_number,
            )
            .first()
        )

        if destination_batch is None:
            destination_batch = StockBatch.objects.create(
                item=source_batch.item,
                warehouse=transfer.destination_warehouse,
                location=destination_location,
                batch_number=source_batch.batch_number,
                expiry_date=source_batch.expiry_date,
                quantity=Decimal("0"),
                unit_cost=source_batch.unit_cost,
                received_at=timezone.now(),
                is_active=True,
            )

        destination_batch.quantity += quantity
        destination_batch.save(
            update_fields=[
                "quantity",
                "updated_at",
            ]
        )

        _create_movement(
            batch=source_batch,
            movement_type="TRANSFER_OUT",
            quantity=quantity,
            performed_by=performed_by,
            reference_type="TRANSFER",
            reference_id=transfer.id,
            reason="Transfer out",
        )

        _create_movement(
            batch=destination_batch,
            movement_type="TRANSFER_IN",
            quantity=quantity,
            performed_by=performed_by,
            reference_type="TRANSFER",
            reference_id=transfer.id,
            reason="Transfer in",
        )

    transfer.status = "COMPLETED"
    transfer.completed_at = timezone.now()
    transfer.save(
        update_fields=[
            "status",
            "completed_at",
        ]
    )

    return transfer


# ============================================================
# READ-ONLY STOCK HELPERS
# ============================================================

def get_available_stock(
    *,
    item_id,
    warehouse_id=None,
):
    """
    Read-only aggregate helper.
    Does not modify the database.
    """

    qs = StockBatch.objects.filter(
        item_id=item_id,
        is_active=True,
    )

    if warehouse_id is not None:
        qs = qs.filter(
            warehouse_id=warehouse_id,
        )

    total = Decimal("0")

    for batch in qs:
        if (
            batch.expiry_date is None
            or batch.expiry_date >= date.today()
        ):
            total += batch.quantity

    return total


def get_batch_stock(batch_id):
    """
    Read-only batch quantity.
    """

    return (
        StockBatch.objects
        .values_list("quantity", flat=True)
        .get(pk=batch_id)
    )


# ============================================================
# PURCHASE WORKFLOW
# ============================================================

from django.db import transaction
from django.db.models import F, Sum


def calculate_purchase_total(purchase):
    """
    حساب إجمالي أمر الشراء من:
    quantity × unit_cost
    """
    total = Decimal("0")

    for item in purchase.items.all():
        total += item.quantity * item.unit_cost

    purchase.total_amount = total
    purchase.save(update_fields=["total_amount", "updated_at"])

    return total


@transaction.atomic
def receive_purchase_item(
    *,
    purchase_item_id,
    quantity,
    location_id,
    performed_by,
    batch_number=None,
    expiry_date=None,
):
    """
    استلام كمية من صنف تابع لأمر شراء.

    يستخدم receive_stock() الموجود حتى يبقى
    منطق المخزون موحدًا في مكان واحد.
    """

    purchase_item = (
        PurchaseItem.objects
        .select_for_update()
        .select_related(
            "purchase",
            "purchase__supplier",
            "purchase__warehouse",
            "item",
        )
        .get(pk=purchase_item_id)
    )

    purchase = purchase_item.purchase

    if purchase.status == Purchase.Status.CANCELLED:
        raise InventoryServiceError(
            "لا يمكن استلام أصناف من أمر شراء ملغى."
        )

    if purchase.status == Purchase.Status.RECEIVED:
        raise InventoryServiceError(
            "أمر الشراء مكتمل الاستلام بالفعل."
        )

    quantity = Decimal(str(quantity))

    if quantity <= 0:
        raise InventoryServiceError(
            "الكمية المستلمة يجب أن تكون أكبر من صفر."
        )

    remaining = (
        purchase_item.quantity
        - purchase_item.received_quantity
    )

    if quantity > remaining:
        raise InventoryServiceError(
            f"الكمية المتبقية هي {remaining} فقط."
        )

    # --------------------------------------------------------
    # حماية PurchaseItem.batch من ربطه بأكثر من Batch
    # --------------------------------------------------------
    existing_batch = purchase_item.batch

    if existing_batch is not None:
        if batch_number:
            if (
                existing_batch.batch_number
                and existing_batch.batch_number != batch_number
            ):
                raise InventoryServiceError(
                    "هذا الصنف تم استلامه مسبقًا في Batch مختلف. "
                    "يجب الاستمرار باستخدام نفس الـ Batch."
                )

        if (
            expiry_date is not None
            and existing_batch.expiry_date is not None
            and existing_batch.expiry_date != expiry_date
        ):
            raise InventoryServiceError(
                "تاريخ الانتهاء لا يطابق الـ Batch المستخدم سابقًا."
            )

        if existing_batch.location_id != location_id:
            raise InventoryServiceError(
                "لا يمكن نقل استلام نفس الصنف إلى موقع تخزين مختلف."
            )

    # --------------------------------------------------------
    # استدعاء خدمة المخزون الموجودة
    # --------------------------------------------------------
    batch, movement = receive_stock(
        item_id=purchase_item.item_id,
        warehouse_id=purchase.warehouse_id,
        location_id=location_id,
        quantity=quantity,
        performed_by=performed_by,
        batch_number=batch_number,
        expiry_date=expiry_date,
        unit_cost=purchase_item.unit_cost,
        supplier_id=purchase.supplier_id,
        reference_type="PURCHASE",
        reference_id=purchase.id,
        reason=(
            f"استلام مشتريات {purchase.purchase_number}"
        ),
    )

    # --------------------------------------------------------
    # تحديث الكمية المستلمة
    # --------------------------------------------------------
    purchase_item.received_quantity = (
        purchase_item.received_quantity + quantity
    )

    if purchase_item.batch_id is None:
        purchase_item.batch = batch

    purchase_item.save(
        update_fields=[
            "received_quantity",
            "batch",
        ]
    )

    # --------------------------------------------------------
    # تحديث حالة أمر الشراء
    # --------------------------------------------------------
    total_ordered = purchase.items.aggregate(
        total=Sum("quantity")
    )["total"] or Decimal("0")

    total_received = purchase.items.aggregate(
        total=Sum("received_quantity")
    )["total"] or Decimal("0")

    if total_received <= 0:
        purchase.status = Purchase.Status.ORDERED
    elif total_received < total_ordered:
        purchase.status = Purchase.Status.PARTIALLY_RECEIVED
    else:
        purchase.status = Purchase.Status.RECEIVED

    purchase.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    # --------------------------------------------------------
    # تحديث إجمالي أمر الشراء
    # --------------------------------------------------------
    calculate_purchase_total(purchase)

    return purchase, purchase_item, batch, movement


# ============================================================
# PURCHASE NUMBER
# ============================================================

def generate_purchase_number():
    """
    إنشاء رقم أمر شراء فريد بصيغة:
    PUR-YYYYMMDD-0001
    """
    from django.utils import timezone

    today = timezone.localdate()
    prefix = f"PUR-{today:%Y%m%d}-"

    last_purchase = (
        Purchase.objects
        .filter(purchase_number__startswith=prefix)
        .order_by("-purchase_number")
        .first()
    )

    if last_purchase:
        try:
            last_number = int(
                last_purchase.purchase_number.rsplit("-", 1)[1]
            )
        except (ValueError, IndexError):
            last_number = 0
    else:
        last_number = 0

    return f"{prefix}{last_number + 1:04d}"
