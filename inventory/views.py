from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Sum, Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.permissions import (
    user_has_access,
    user_has_permission,
)

from .models import (
    InventoryCategory,
    UnitOfMeasure,
    Supplier,
    InventoryItem,
    Warehouse,
    StorageLocation,
    StockBatch,
    StockMovement,
    StockTransfer,
    Purchase,
    PurchaseItem,
)

from .forms import (
    InventoryCategoryForm,
    UnitOfMeasureForm,
    SupplierForm,
    InventoryItemForm,
    WarehouseForm,
    StorageLocationForm,
    StockBatchFilterForm,
    ReceiveStockForm,
    IssueStockForm,
    ReturnStockForm,
    AdjustmentStockForm,
    TransferStockForm,
    PurchaseForm,
    PurchaseItemForm,
    PurchaseReceiveForm,
)

from .services import (
    receive_stock,
    issue_stock,
    return_stock,
    adjust_stock,
    create_transfer,
    approve_transfer,
    complete_transfer,
    InventoryServiceError,
    calculate_purchase_total,
    receive_purchase_item,
    generate_purchase_number,
)


# ============================================================
# PERMISSIONS
# ============================================================

def _require_inventory_access(request):
    if not user_has_access(request.user, "inventory"):
        raise PermissionDenied


def _require_permission(request, permission):
    _require_inventory_access(request)

    if not user_has_permission(request.user, permission):
        raise PermissionDenied


# ============================================================
# COMMON CONTEXT
# ============================================================

def _base_context():
    return {
        "inventory_section": True,
    }


# ============================================================
# DASHBOARD
# ============================================================

@login_required
def dashboard(request):
    _require_permission(request, "inventory.view")

    today = date.today()
    expiry_limit = today + timedelta(days=30)

    active_items = InventoryItem.objects.filter(
        is_active=True
    ).count()

    active_warehouses = Warehouse.objects.filter(
        is_active=True
    ).count()

    active_batches = StockBatch.objects.filter(
        is_active=True,
        item__is_active=True,
    ).select_related("item", "warehouse", "location")

    total_stock = Decimal("0")
    total_stock_value = Decimal("0")
    low_stock_count = 0
    expired_count = 0
    expiring_count = 0

    item_totals = {}

    for batch in active_batches:
        quantity = batch.quantity or Decimal("0")

        if batch.expiry_date and batch.expiry_date < today:
            expired_count += 1
            continue

        total_stock += quantity
        total_stock_value += quantity * (batch.unit_cost or Decimal("0"))

        item_id = batch.item_id
        item_totals[item_id] = (
            item_totals.get(item_id, Decimal("0")) + quantity
        )

        if (
            batch.expiry_date
            and today <= batch.expiry_date <= expiry_limit
        ):
            expiring_count += 1

    for item in InventoryItem.objects.filter(
        is_active=True
    ).only("id", "reorder_level"):
        current = item_totals.get(
            item.id,
            Decimal("0"),
        )

        reorder = item.reorder_level or Decimal("0")

        if reorder > 0 and current <= reorder:
            low_stock_count += 1

    # ========================================================
    # INVENTORY ALERTS
    # ========================================================

    low_stock_items = []

    for item in InventoryItem.objects.filter(
        is_active=True,
        reorder_level__gt=0,
    ).only(
        "id",
        "code",
        "name_ar",
        "name_en",
        "reorder_level",
    ):
        current_quantity = item_totals.get(
            item.id,
            Decimal("0"),
        )

        if current_quantity <= item.reorder_level:
            item.current_quantity = current_quantity
            low_stock_items.append(item)

    low_stock_items.sort(
        key=lambda item: (
            item.reorder_level - item.current_quantity
        ),
        reverse=True,
    )

    expired_batches = list(
        StockBatch.objects.filter(
            is_active=True,
            item__is_active=True,
            expiry_date__lt=today,
        )
        .select_related(
            "item",
            "warehouse",
            "location",
        )
        .order_by("expiry_date", "item__name_ar")[:20]
    )

    expiring_batches = list(
        StockBatch.objects.filter(
            is_active=True,
            item__is_active=True,
            expiry_date__gte=today,
            expiry_date__lte=expiry_limit,
        )
        .select_related(
            "item",
            "warehouse",
            "location",
        )
        .order_by("expiry_date", "item__name_ar")[:20]
    )

    pending_transfers = StockTransfer.objects.filter(
        status__in=["REQUESTED", "APPROVED"]
    ).count()

    recent_movements = (
        StockMovement.objects
        .select_related(
            "batch",
            "batch__item",
            "batch__warehouse",
            "performed_by",
        )
        .order_by("-created_at")[:10]
    )

    context = {
        **_base_context(),
        "active_items": active_items,
        "active_warehouses": active_warehouses,
        "total_stock": total_stock,
        "total_stock_value": total_stock_value,
        "low_stock_count": low_stock_count,
        "expired_count": expired_count,
        "expiring_count": expiring_count,
        "pending_transfers": pending_transfers,
        "low_stock_items": low_stock_items,
        "expired_batches": expired_batches,
        "expiring_batches": expiring_batches,
        "recent_movements": recent_movements,
    }

    return render(
        request,
        "inventory/dashboard.html",
        context,
    )


# ============================================================
# CATEGORIES
# ============================================================

@login_required
def category_list(request):
    _require_permission(request, "inventory.view")

    categories = (
        InventoryCategory.objects
        .select_related("parent")
        .order_by("name_ar")
    )

    return render(
        request,
        "inventory/category_list.html",
        {
            **_base_context(),
            "categories": categories,
        },
    )


@login_required
def category_create(request):
    _require_permission(request, "inventory.create")

    if request.method == "POST":
        form = InventoryCategoryForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "تمت إضافة التصنيف بنجاح.",
            )
            return redirect("inventory:category_list")
    else:
        form = InventoryCategoryForm()

    return render(
        request,
        "inventory/category_form.html",
        {
            **_base_context(),
            "form": form,
            "page_title": "إضافة تصنيف",
            "submit_label": "حفظ التصنيف",
        },
    )


@login_required
def category_edit(request, pk):
    _require_permission(request, "inventory.create")

    obj = get_object_or_404(
        InventoryCategory,
        pk=pk,
    )

    if request.method == "POST":
        form = InventoryCategoryForm(
            request.POST,
            instance=obj,
        )

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "تم تحديث التصنيف بنجاح.",
            )
            return redirect("inventory:category_list")
    else:
        form = InventoryCategoryForm(instance=obj)

    return render(
        request,
        "inventory/category_form.html",
        {
            **_base_context(),
            "form": form,
            "page_title": "تعديل التصنيف",
            "submit_label": "حفظ التعديلات",
        },
    )


# ============================================================
# UNITS
# ============================================================

@login_required
def unit_list(request):
    _require_permission(request, "inventory.view")

    units = UnitOfMeasure.objects.order_by("name_ar")

    return render(
        request,
        "inventory/unit_list.html",
        {
            **_base_context(),
            "units": units,
        },
    )


@login_required
def unit_create(request):
    _require_permission(request, "inventory.create")

    if request.method == "POST":
        form = UnitOfMeasureForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "تمت إضافة وحدة القياس بنجاح.",
            )
            return redirect("inventory:unit_list")
    else:
        form = UnitOfMeasureForm()

    return render(
        request,
        "inventory/unit_form.html",
        {
            **_base_context(),
            "form": form,
            "page_title": "إضافة وحدة قياس",
            "submit_label": "حفظ الوحدة",
        },
    )


@login_required
def unit_edit(request, pk):
    _require_permission(request, "inventory.create")

    obj = get_object_or_404(
        UnitOfMeasure,
        pk=pk,
    )

    if request.method == "POST":
        form = UnitOfMeasureForm(
            request.POST,
            instance=obj,
        )

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "تم تحديث وحدة القياس بنجاح.",
            )
            return redirect("inventory:unit_list")
    else:
        form = UnitOfMeasureForm(instance=obj)

    return render(
        request,
        "inventory/unit_form.html",
        {
            **_base_context(),
            "form": form,
            "page_title": "تعديل وحدة القياس",
            "submit_label": "حفظ التعديلات",
        },
    )


# ============================================================
# SUPPLIERS
# ============================================================

@login_required
def supplier_list(request):
    _require_permission(request, "inventory.view")

    suppliers = Supplier.objects.order_by("name_ar")

    return render(
        request,
        "inventory/supplier_list.html",
        {
            **_base_context(),
            "suppliers": suppliers,
        },
    )


@login_required
def supplier_create(request):
    _require_permission(request, "inventory.create")

    if request.method == "POST":
        form = SupplierForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "تمت إضافة المورد بنجاح.",
            )
            return redirect("inventory:supplier_list")
    else:
        form = SupplierForm()

    return render(
        request,
        "inventory/supplier_form.html",
        {
            **_base_context(),
            "form": form,
            "page_title": "إضافة مورد",
            "submit_label": "حفظ المورد",
        },
    )


@login_required
def supplier_edit(request, pk):
    _require_permission(request, "inventory.create")

    obj = get_object_or_404(
        Supplier,
        pk=pk,
    )

    if request.method == "POST":
        form = SupplierForm(
            request.POST,
            instance=obj,
        )

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "تم تحديث المورد بنجاح.",
            )
            return redirect("inventory:supplier_list")
    else:
        form = SupplierForm(instance=obj)

    return render(
        request,
        "inventory/supplier_form.html",
        {
            **_base_context(),
            "form": form,
            "page_title": "تعديل المورد",
            "submit_label": "حفظ التعديلات",
        },
    )


# ============================================================
# ITEMS
# ============================================================

@login_required
def item_list(request):
    _require_permission(request, "inventory.view")

    qs = (
        InventoryItem.objects
        .select_related(
            "category",
            "unit",
        )
        .order_by("name_ar")
    )

    q = request.GET.get("q", "").strip()

    if q:
        qs = qs.filter(
            Q(name_ar__icontains=q)
            | Q(name_en__icontains=q)
            | Q(code__icontains=q)
            | Q(barcode__icontains=q)
        )

    return render(
        request,
        "inventory/item_list.html",
        {
            **_base_context(),
            "items": qs,
            "search_query": q,
        },
    )


@login_required
def item_create(request):
    _require_permission(request, "inventory.create")

    if request.method == "POST":
        form = InventoryItemForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "تمت إضافة الصنف بنجاح.",
            )
            return redirect("inventory:item_list")
    else:
        form = InventoryItemForm()

    return render(
        request,
        "inventory/item_form.html",
        {
            **_base_context(),
            "form": form,
            "page_title": "إضافة صنف",
            "submit_label": "حفظ الصنف",
        },
    )


@login_required
def item_edit(request, pk):
    _require_permission(request, "inventory.create")

    obj = get_object_or_404(
        InventoryItem,
        pk=pk,
    )

    if request.method == "POST":
        form = InventoryItemForm(
            request.POST,
            instance=obj,
        )

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "تم تحديث الصنف بنجاح.",
            )
            return redirect("inventory:item_list")
    else:
        form = InventoryItemForm(instance=obj)

    return render(
        request,
        "inventory/item_form.html",
        {
            **_base_context(),
            "form": form,
            "page_title": "تعديل الصنف",
            "submit_label": "حفظ التعديلات",
        },
    )


# ============================================================
# WAREHOUSES
# ============================================================

@login_required
def warehouse_list(request):
    _require_permission(request, "inventory.view")

    warehouses = (
        Warehouse.objects
        .select_related("department")
        .order_by("name_ar")
    )

    return render(
        request,
        "inventory/warehouse_list.html",
        {
            **_base_context(),
            "warehouses": warehouses,
        },
    )


@login_required
def warehouse_create(request):
    _require_permission(request, "inventory.create")

    if request.method == "POST":
        form = WarehouseForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "تمت إضافة المستودع بنجاح.",
            )
            return redirect("inventory:warehouse_list")
    else:
        form = WarehouseForm()

    return render(
        request,
        "inventory/warehouse_form.html",
        {
            **_base_context(),
            "form": form,
            "page_title": "إضافة مستودع",
            "submit_label": "حفظ المستودع",
        },
    )


@login_required
def warehouse_edit(request, pk):
    _require_permission(request, "inventory.create")

    obj = get_object_or_404(
        Warehouse,
        pk=pk,
    )

    if request.method == "POST":
        form = WarehouseForm(
            request.POST,
            instance=obj,
        )

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "تم تحديث المستودع بنجاح.",
            )
            return redirect("inventory:warehouse_list")
    else:
        form = WarehouseForm(instance=obj)

    return render(
        request,
        "inventory/warehouse_form.html",
        {
            **_base_context(),
            "form": form,
            "page_title": "تعديل المستودع",
            "submit_label": "حفظ التعديلات",
        },
    )


# ============================================================
# STORAGE LOCATIONS
# ============================================================

@login_required
def location_list(request):
    _require_permission(request, "inventory.view")

    locations = (
        StorageLocation.objects
        .select_related("warehouse")
        .order_by(
            "warehouse__name_ar",
            "name_ar",
        )
    )

    return render(
        request,
        "inventory/location_list.html",
        {
            **_base_context(),
            "locations": locations,
        },
    )


@login_required
def location_create(request):
    _require_permission(request, "inventory.create")

    if request.method == "POST":
        form = StorageLocationForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "تمت إضافة موقع التخزين بنجاح.",
            )
            return redirect("inventory:location_list")
    else:
        form = StorageLocationForm()

    return render(
        request,
        "inventory/location_form.html",
        {
            **_base_context(),
            "form": form,
            "page_title": "إضافة موقع تخزين",
            "submit_label": "حفظ الموقع",
        },
    )


@login_required
def location_edit(request, pk):
    _require_permission(request, "inventory.create")

    obj = get_object_or_404(
        StorageLocation,
        pk=pk,
    )

    if request.method == "POST":
        form = StorageLocationForm(
            request.POST,
            instance=obj,
        )

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "تم تحديث موقع التخزين بنجاح.",
            )
            return redirect("inventory:location_list")
    else:
        form = StorageLocationForm(instance=obj)

    return render(
        request,
        "inventory/location_form.html",
        {
            **_base_context(),
            "form": form,
            "page_title": "تعديل موقع التخزين",
            "submit_label": "حفظ التعديلات",
        },
    )


# ============================================================
# STOCK
# ============================================================

@login_required
def stock_list(request):
    _require_permission(request, "inventory.view")

    form = StockBatchFilterForm(request.GET or None)

    qs = (
        StockBatch.objects
        .select_related(
            "item",
            "warehouse",
            "location",
            "supplier",
        )
        .order_by(
            "item__name_ar",
            "warehouse__name_ar",
            "batch_number",
        )
    )

    if form.is_valid():
        item = form.cleaned_data.get("item")
        warehouse = form.cleaned_data.get("warehouse")
        batch_number = form.cleaned_data.get("batch_number")

        if item:
            qs = qs.filter(item=item)

        if warehouse:
            qs = qs.filter(warehouse=warehouse)

        if batch_number:
            qs = qs.filter(
                batch_number__icontains=batch_number
            )

    return render(
        request,
        "inventory/stock_list.html",
        {
            **_base_context(),
            "form": form,
            "batches": qs,
            "today": date.today(),
        },
    )


# ============================================================
# RECEIVE
# ============================================================

@login_required
def receive(request):
    _require_permission(request, "inventory.movement")

    if request.method == "POST":
        form = ReceiveStockForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data

            try:
                batch, movement = receive_stock(
                    item_id=data["item"].id,
                    warehouse_id=data["warehouse"].id,
                    location_id=data["location"].id,
                    quantity=data["quantity"],
                    performed_by=request.user,
                    batch_number=data.get("batch_number"),
                    expiry_date=data.get("expiry_date"),
                    unit_cost=data.get("unit_cost") or Decimal("0"),
                    supplier_id=(
                        data["supplier"].id
                        if data.get("supplier")
                        else None
                    ),
                    reference_type="MANUAL",
                    reason=data.get("reason", ""),
                )

                messages.success(
                    request,
                    f"تم استقبال {data['quantity']} بنجاح.",
                )

                return redirect("inventory:stock_list")

            except InventoryServiceError as exc:
                form.add_error(
                    None,
                    str(exc),
                )
    else:
        form = ReceiveStockForm()

    return render(
        request,
        "inventory/receive.html",
        {
            **_base_context(),
            "form": form,
        },
    )


# ============================================================
# ISSUE
# ============================================================

@login_required
def issue(request):
    _require_permission(request, "inventory.movement")

    if request.method == "POST":
        form = IssueStockForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data

            try:
                issue_stock(
                    batch_id=data["batch"].id,
                    quantity=data["quantity"],
                    performed_by=request.user,
                    reference_type="MANUAL",
                    reason=data.get("reason", ""),
                )

                messages.success(
                    request,
                    "تم صرف المخزون بنجاح.",
                )

                return redirect("inventory:stock_list")

            except InventoryServiceError as exc:
                form.add_error(
                    None,
                    str(exc),
                )
    else:
        form = IssueStockForm()

    return render(
        request,
        "inventory/issue.html",
        {
            **_base_context(),
            "form": form,
        },
    )


# ============================================================
# RETURN
# ============================================================

@login_required
def return_stock_view(request):
    _require_permission(request, "inventory.movement")

    if request.method == "POST":
        form = ReturnStockForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data

            try:
                return_stock(
                    batch_id=data["batch"].id,
                    quantity=data["quantity"],
                    performed_by=request.user,
                    reference_type="MANUAL",
                    reason=data.get("reason", ""),
                )

                messages.success(
                    request,
                    "تم إرجاع المخزون بنجاح.",
                )

                return redirect("inventory:stock_list")

            except InventoryServiceError as exc:
                form.add_error(
                    None,
                    str(exc),
                )
    else:
        form = ReturnStockForm()

    return render(
        request,
        "inventory/return.html",
        {
            **_base_context(),
            "form": form,
        },
    )


# ============================================================
# ADJUSTMENT
# ============================================================

@login_required
def adjustment(request):
    _require_permission(request, "inventory.movement")

    if request.method == "POST":
        form = AdjustmentStockForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data

            try:
                adjust_stock(
                    batch_id=data["batch"].id,
                    new_quantity=data["new_quantity"],
                    performed_by=request.user,
                    reason=data["reason"],
                )

                messages.success(
                    request,
                    "تم تعديل كمية المخزون وتسجيل الحركة.",
                )

                return redirect("inventory:stock_list")

            except InventoryServiceError as exc:
                form.add_error(
                    None,
                    str(exc),
                )
    else:
        form = AdjustmentStockForm()

    return render(
        request,
        "inventory/adjustment.html",
        {
            **_base_context(),
            "form": form,
        },
    )


# ============================================================
# TRANSFERS
# ============================================================

@login_required
def transfer_list(request):
    _require_permission(request, "inventory.view")

    transfers = (
        StockTransfer.objects
        .select_related(
            "source_warehouse",
            "destination_warehouse",
            "requested_by",
            "approved_by",
        )
        .prefetch_related(
            "items",
            "items__item",
            "items__batch",
        )
        .order_by("-created_at")
    )

    return render(
        request,
        "inventory/transfer_list.html",
        {
            **_base_context(),
            "transfers": transfers,
        },
    )


@login_required
def transfer_create(request):
    _require_permission(request, "inventory.movement")

    if request.method == "POST":
        form = TransferStockForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data

            try:
                create_transfer(
                    source_warehouse_id=data[
                        "source_warehouse"
                    ].id,
                    destination_warehouse_id=data[
                        "destination_warehouse"
                    ].id,
                    batch_id=data["batch"].id,
                    quantity=data["quantity"],
                    requested_by=request.user,
                )

                messages.success(
                    request,
                    "تم إنشاء طلب التحويل بنجاح.",
                )

                return redirect(
                    "inventory:transfer_list"
                )

            except InventoryServiceError as exc:
                form.add_error(
                    None,
                    str(exc),
                )
    else:
        form = TransferStockForm()

    return render(
        request,
        "inventory/transfer_form.html",
        {
            **_base_context(),
            "form": form,
        },
    )


@login_required
def transfer_approve(request, pk):
    _require_permission(request, "inventory.movement")

    if request.method != "POST":
        return redirect("inventory:transfer_list")

    try:
        approve_transfer(
            transfer_id=pk,
            approved_by=request.user,
        )

        messages.success(
            request,
            "تم اعتماد التحويل.",
        )

    except InventoryServiceError as exc:
        messages.error(
            request,
            str(exc),
        )

    return redirect("inventory:transfer_list")


@login_required
def transfer_complete(request, pk):
    _require_permission(request, "inventory.movement")

    if request.method != "POST":
        return redirect("inventory:transfer_list")

    try:
        complete_transfer(
            transfer_id=pk,
            performed_by=request.user,
        )

        messages.success(
            request,
            "تم إكمال التحويل ونقل الكمية.",
        )

    except InventoryServiceError as exc:
        messages.error(
            request,
            str(exc),
        )

    return redirect("inventory:transfer_list")


# ============================================================
# MOVEMENTS
# ============================================================

@login_required
def movement_list(request):
    _require_permission(request, "inventory.view")

    movements = (
        StockMovement.objects
        .select_related(
            "batch",
            "batch__item",
            "batch__warehouse",
            "batch__location",
            "performed_by",
        )
        .order_by("-created_at")
    )

    q = request.GET.get("q", "").strip()
    movement_type = request.GET.get("movement_type", "").strip()
    warehouse_id = request.GET.get("warehouse", "").strip()
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()

    if q:
        movements = movements.filter(
            Q(batch__item__name_ar__icontains=q)
            | Q(batch__item__name_en__icontains=q)
            | Q(batch__item__code__icontains=q)
            | Q(reference_type__icontains=q)
            | Q(reason__icontains=q)
        )

    if movement_type:
        movements = movements.filter(
            movement_type=movement_type
        )

    if warehouse_id:
        movements = movements.filter(
            batch__warehouse_id=warehouse_id
        )

    if date_from:
        movements = movements.filter(
            created_at__date__gte=date_from
        )

    if date_to:
        movements = movements.filter(
            created_at__date__lte=date_to
        )

    movement_totals = {
        "count": movements.count(),
        "receipt": movements.filter(
            movement_type=StockMovement.MovementType.RECEIPT
        ).aggregate(total=Sum("quantity"))["total"] or 0,
        "issue": movements.filter(
            movement_type=StockMovement.MovementType.ISSUE
        ).aggregate(total=Sum("quantity"))["total"] or 0,
        "return": movements.filter(
            movement_type=StockMovement.MovementType.RETURN
        ).aggregate(total=Sum("quantity"))["total"] or 0,
        "transfer_in": movements.filter(
            movement_type=StockMovement.MovementType.TRANSFER_IN
        ).aggregate(total=Sum("quantity"))["total"] or 0,
        "transfer_out": movements.filter(
            movement_type=StockMovement.MovementType.TRANSFER_OUT
        ).aggregate(total=Sum("quantity"))["total"] or 0,
        "adjustment": movements.filter(
            movement_type=StockMovement.MovementType.ADJUSTMENT
        ).aggregate(total=Sum("quantity"))["total"] or 0,
        "disposal": movements.filter(
            movement_type=StockMovement.MovementType.DISPOSAL
        ).aggregate(total=Sum("quantity"))["total"] or 0,
        "expiry": movements.filter(
            movement_type=StockMovement.MovementType.EXPIRY
        ).aggregate(total=Sum("quantity"))["total"] or 0,
    }

    return render(
        request,
        "inventory/movement_list.html",
        {
            **_base_context(),
            "movements": movements[:500],
            "movement_totals": movement_totals,
            "search_query": q,
            "movement_type": movement_type,
            "warehouse_id": warehouse_id,
            "date_from": date_from,
            "date_to": date_to,
            "movement_types": StockMovement.MovementType.choices,
            "warehouses": Warehouse.objects.filter(
                is_active=True
            ).order_by("name_ar"),
        },
    )

# ============================================================
# PURCHASE WORKFLOW
# ============================================================

from django.db import transaction
from django.contrib import messages
from django.shortcuts import get_object_or_404


@login_required
def purchase_list(request):
    _require_permission(request, "inventory.view")

    purchases = (
        Purchase.objects
        .select_related(
            "supplier",
            "warehouse",
            "created_by",
        )
        .prefetch_related("items")
        .order_by("-purchase_date", "-id")
    )

    search = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    supplier_id = request.GET.get("supplier", "").strip()
    warehouse_id = request.GET.get("warehouse", "").strip()

    if search:
        purchases = purchases.filter(
            Q(purchase_number__icontains=search)
            | Q(supplier__name_ar__icontains=search)
            | Q(supplier__name_en__icontains=search)
        )

    if status:
        purchases = purchases.filter(status=status)

    if supplier_id:
        purchases = purchases.filter(supplier_id=supplier_id)

    if warehouse_id:
        purchases = purchases.filter(warehouse_id=warehouse_id)

    return render(
        request,
        "inventory/purchase_list.html",
        {
            "purchases": purchases,
            "search": search,
            "status": status,
            "supplier_id": supplier_id,
            "warehouse_id": warehouse_id,
            "purchase_statuses": Purchase.Status.choices,
            "suppliers": Supplier.objects.filter(
                is_active=True
            ).order_by("name_ar"),
            "warehouses": Warehouse.objects.filter(
                is_active=True
            ).order_by("name_ar"),
        },
    )


@login_required
def purchase_create(request):
    _require_permission(request, "inventory.view")

    if request.method == "POST":
        form = PurchaseForm(request.POST)

        if form.is_valid():
            purchase = form.save(commit=False)

            purchase.purchase_number = (
                generate_purchase_number()
            )
            purchase.status = Purchase.Status.DRAFT
            purchase.total_amount = Decimal("0")
            purchase.created_by = request.user
            purchase.save()

            messages.success(
                request,
                f"تم إنشاء أمر الشراء {purchase.purchase_number} بنجاح.",
            )

            return redirect(
                "inventory:purchase_detail",
                pk=purchase.pk,
            )
    else:
        form = PurchaseForm()

    return render(
        request,
        "inventory/purchase_form.html",
        {
            "form": form,
        },
    )


@login_required
def purchase_detail(request, pk):
    _require_permission(request, "inventory.view")

    purchase = get_object_or_404(
        Purchase.objects
        .select_related(
            "supplier",
            "warehouse",
            "created_by",
        )
        .prefetch_related(
            "items__item",
            "items__batch",
        ),
        pk=pk,
    )

    return render(
        request,
        "inventory/purchase_detail.html",
        {
            "purchase": purchase,
        },
    )


@login_required
def purchase_item_create(request, purchase_id):
    _require_permission(request, "inventory.view")

    purchase = get_object_or_404(
        Purchase,
        pk=purchase_id,
    )

    if purchase.status not in [
        Purchase.Status.DRAFT,
        Purchase.Status.ORDERED,
        Purchase.Status.PARTIALLY_RECEIVED,
    ]:
        messages.error(
            request,
            "لا يمكن إضافة أصناف إلى أمر الشراء بهذه الحالة.",
        )

        return redirect(
            "inventory:purchase_detail",
            pk=purchase.pk,
        )

    if request.method == "POST":
        form = PurchaseItemForm(
            request.POST,
            purchase=purchase,
        )

        if form.is_valid():
            item = form.save(commit=False)
            item.purchase = purchase
            item.received_quantity = Decimal("0")
            item.save()

            calculate_purchase_total(purchase)

            messages.success(
                request,
                "تمت إضافة الصنف إلى أمر الشراء بنجاح.",
            )

            return redirect(
                "inventory:purchase_detail",
                pk=purchase.pk,
            )
    else:
        form = PurchaseItemForm(
            purchase=purchase,
        )

    return render(
        request,
        "inventory/purchase_item_form.html",
        {
            "form": form,
            "purchase": purchase,
        },
    )


@login_required
def purchase_order(request, pk):
    _require_permission(request, "inventory.movement")

    if request.method != "POST":
        return redirect(
            "inventory:purchase_detail",
            pk=pk,
        )

    purchase = get_object_or_404(
        Purchase,
        pk=pk,
    )

    if purchase.status != Purchase.Status.DRAFT:
        messages.error(
            request,
            "لا يمكن تحويل أمر الشراء إلى Ordered من حالته الحالية.",
        )

        return redirect(
            "inventory:purchase_detail",
            pk=purchase.pk,
        )

    if not purchase.items.exists():
        messages.error(
            request,
            "لا يمكن اعتماد أمر شراء بدون أصناف.",
        )

        return redirect(
            "inventory:purchase_detail",
            pk=purchase.pk,
        )

    purchase.status = Purchase.Status.ORDERED
    purchase.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    messages.success(
        request,
        f"تم اعتماد أمر الشراء {purchase.purchase_number}.",
    )

    return redirect(
        "inventory:purchase_detail",
        pk=purchase.pk,
    )


# ============================================================
# PURCHASE RECEIVING
# ============================================================

@login_required
def purchase_item_receive(request, purchase_item_id):
    _require_permission(request, "inventory.movement")

    purchase_item = get_object_or_404(
        PurchaseItem.objects
        .select_related(
            "purchase",
            "purchase__supplier",
            "purchase__warehouse",
            "item",
            "batch",
        ),
        pk=purchase_item_id,
    )

    purchase = purchase_item.purchase

    remaining = (
        purchase_item.quantity
        - purchase_item.received_quantity
    )

    if purchase.status in [
        Purchase.Status.CANCELLED,
        Purchase.Status.RECEIVED,
    ] or remaining <= 0:
        messages.error(
            request,
            "لا توجد كمية متبقية قابلة للاستلام لهذا الصنف.",
        )

        return redirect(
            "inventory:purchase_detail",
            pk=purchase.pk,
        )

    if request.method == "POST":
        form = PurchaseReceiveForm(
            request.POST,
            purchase_item=purchase_item,
        )

        if form.is_valid():
            data = form.cleaned_data

            try:
                (
                    purchase,
                    purchase_item,
                    batch,
                    movement,
                ) = receive_purchase_item(
                    purchase_item_id=purchase_item.pk,
                    quantity=data["quantity"],
                    location_id=data["location"].pk,
                    performed_by=request.user,
                    batch_number=(
                        data.get("batch_number") or None
                    ),
                    expiry_date=data.get("expiry_date"),
                )

                messages.success(
                    request,
                    (
                        f"تم استلام {data['quantity']} "
                        f"من الصنف بنجاح."
                    ),
                )

                return redirect(
                    "inventory:purchase_detail",
                    pk=purchase.pk,
                )

            except InventoryServiceError as exc:
                form.add_error(
                    None,
                    str(exc),
                )

    else:
        initial = {}

        if purchase_item.batch is not None:
            initial["batch_number"] = (
                purchase_item.batch.batch_number or ""
            )

            initial["expiry_date"] = (
                purchase_item.batch.expiry_date
            )

            initial["location"] = (
                purchase_item.batch.location_id
            )

        form = PurchaseReceiveForm(
            purchase_item=purchase_item,
            initial=initial,
        )

    return render(
        request,
        "inventory/purchase_receive.html",
        {
            "form": form,
            "purchase": purchase,
            "purchase_item": purchase_item,
            "remaining": remaining,
        },
    )

# ========================================================
# INVENTORY EXPIRY REPORTS
# ========================================================

@login_required
def expired_list(request):
    _require_permission(request, "inventory.view")

    today = date.today()

    rows = (
        StockBatch.objects
        .filter(
            is_active=True,
            item__is_active=True,
            expiry_date__lt=today,
        )
        .select_related(
            "item",
            "warehouse",
            "location",
        )
        .order_by(
            "expiry_date",
            "item__name_ar",
        )
    )

    return render(
        request,
        "inventory/expired.html",
        {
            **_base_context(),
            "rows": rows,
            "today": today,
        },
    )


@login_required
def expiring_list(request):
    _require_permission(request, "inventory.view")

    today = date.today()
    limit = today + timedelta(days=30)

    rows = (
        StockBatch.objects
        .filter(
            is_active=True,
            item__is_active=True,
            expiry_date__gte=today,
            expiry_date__lte=limit,
        )
        .select_related(
            "item",
            "warehouse",
            "location",
        )
        .order_by(
            "expiry_date",
            "item__name_ar",
        )
    )

    return render(
        request,
        "inventory/expiring.html",
        {
            **_base_context(),
            "rows": rows,
            "today": today,
            "limit": limit,
        },
    )

@login_required
def stock_value_report(request):
    _require_permission(request, "inventory.view")

    batches = (
        StockBatch.objects
        .filter(
            is_active=True,
            item__is_active=True,
            quantity__gt=0,
        )
        .select_related(
            "item",
            "item__category",
            "item__unit",
            "warehouse",
            "location",
            "supplier",
        )
        .order_by("item__name_ar", "warehouse__name_ar", "expiry_date")
    )

    q = request.GET.get("q", "").strip()
    warehouse_id = request.GET.get("warehouse", "").strip()

    if q:
        batches = batches.filter(
            Q(item__name_ar__icontains=q)
            | Q(item__name_en__icontains=q)
            | Q(item__code__icontains=q)
            | Q(item__barcode__icontains=q)
            | Q(batch_number__icontains=q)
        )

    if warehouse_id:
        batches = batches.filter(warehouse_id=warehouse_id)

    rows = []
    total_quantity = Decimal("0")
    total_value = Decimal("0")

    for batch in batches:
        quantity = batch.quantity or Decimal("0")
        unit_cost = batch.unit_cost or Decimal("0")
        value = quantity * unit_cost

        rows.append({
            "batch": batch,
            "quantity": quantity,
            "unit_cost": unit_cost,
            "value": value,
        })

        total_quantity += quantity
        total_value += value

    return render(
        request,
        "inventory/stock_value_report.html",
        {
            **_base_context(),
            "rows": rows,
            "search_query": q,
            "warehouse_id": warehouse_id,
            "warehouses": Warehouse.objects.filter(
                is_active=True
            ).order_by("name_ar"),
            "total_quantity": total_quantity,
            "total_value": total_value,
        },
    )

@login_required
def stock_summary_report(request):
    _require_permission(request, "inventory.view")

    batches = (
        StockBatch.objects
        .filter(
            is_active=True,
            item__is_active=True,
            quantity__gt=0,
        )
        .select_related("item", "item__unit", "item__category", "warehouse")
        .order_by("item__name_ar")
    )

    q = request.GET.get("q", "").strip()
    warehouse_id = request.GET.get("warehouse", "").strip()

    if q:
        batches = batches.filter(
            Q(item__name_ar__icontains=q)
            | Q(item__name_en__icontains=q)
            | Q(item__code__icontains=q)
            | Q(item__barcode__icontains=q)
        )

    if warehouse_id:
        batches = batches.filter(warehouse_id=warehouse_id)

    summary = {}

    for batch in batches:
        item_id = batch.item_id

        if item_id not in summary:
            summary[item_id] = {
                "item": batch.item,
                "quantity": Decimal("0"),
                "value": Decimal("0"),
                "batches": 0,
            }

        quantity = batch.quantity or Decimal("0")
        unit_cost = batch.unit_cost or Decimal("0")

        summary[item_id]["quantity"] += quantity
        summary[item_id]["value"] += quantity * unit_cost
        summary[item_id]["batches"] += 1

    rows = []

    for data in summary.values():
        quantity = data["quantity"]
        value = data["value"]

        data["average_cost"] = (
            value / quantity if quantity > 0 else Decimal("0")
        )

        rows.append(data)

    rows.sort(key=lambda row: row["item"].name_ar)

    total_quantity = sum(
        (row["quantity"] for row in rows),
        Decimal("0"),
    )

    total_value = sum(
        (row["value"] for row in rows),
        Decimal("0"),
    )

    return render(
        request,
        "inventory/stock_summary_report.html",
        {
            **_base_context(),
            "rows": rows,
            "search_query": q,
            "warehouse_id": warehouse_id,
            "warehouses": Warehouse.objects.filter(
                is_active=True
            ).order_by("name_ar"),
            "total_items": len(rows),
            "total_quantity": total_quantity,
            "total_value": total_value,
        },
    )

