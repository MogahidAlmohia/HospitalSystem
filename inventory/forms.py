from django import forms

from .models import (
    InventoryCategory,
    UnitOfMeasure,
    Supplier,
    InventoryItem,
    Warehouse,
    StorageLocation,
    StockBatch,
    Purchase,
    PurchaseItem,
)


class BootstrapMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            css = field.widget.attrs.get("class", "")

            if isinstance(field.widget, forms.Select):
                css = f"{css} form-select".strip()
            else:
                css = f"{css} form-control".strip()

            field.widget.attrs["class"] = css


class InventoryCategoryForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = InventoryCategory
        fields = [
            "name_ar",
            "name_en",
            "code",
            "parent",
            "description",
            "is_active",
        ]
        labels = {
            "name_ar": "اسم التصنيف بالعربية",
            "name_en": "اسم التصنيف بالإنجليزية",
            "code": "رمز التصنيف",
            "parent": "التصنيف الأب",
            "description": "الوصف",
            "is_active": "نشط",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class UnitOfMeasureForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = UnitOfMeasure
        fields = [
            "code",
            "name_ar",
            "name_en",
            "is_active",
        ]
        labels = {
            "code": "رمز الوحدة",
            "name_ar": "اسم الوحدة بالعربية",
            "name_en": "اسم الوحدة بالإنجليزية",
            "is_active": "نشط",
        }


class SupplierForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Supplier
        fields = [
            "name_ar",
            "name_en",
            "code",
            "phone",
            "email",
            "address",
            "contact_person",
            "tax_number",
            "notes",
            "is_active",
        ]
        labels = {
            "name_ar": "اسم المورد بالعربية",
            "name_en": "اسم المورد بالإنجليزية",
            "code": "رمز المورد",
            "phone": "الهاتف",
            "email": "البريد الإلكتروني",
            "address": "العنوان",
            "contact_person": "اسم جهة الاتصال",
            "tax_number": "الرقم الضريبي",
            "notes": "ملاحظات",
            "is_active": "نشط",
        }
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class InventoryItemForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = [
            "code",
            "name_ar",
            "name_en",
            "category",
            "unit",
            "item_type",
            "description",
            "manufacturer",
            "barcode",
            "reorder_level",
            "maximum_level",
            "requires_batch",
            "requires_expiry",
            "is_active",
        ]
        labels = {
            "code": "رمز الصنف",
            "name_ar": "اسم الصنف بالعربية",
            "name_en": "اسم الصنف بالإنجليزية",
            "category": "التصنيف",
            "unit": "وحدة القياس",
            "item_type": "نوع الصنف",
            "description": "الوصف",
            "manufacturer": "الشركة المصنعة",
            "barcode": "الباركود",
            "reorder_level": "حد إعادة الطلب",
            "maximum_level": "الحد الأقصى",
            "requires_batch": "يتطلب Batch",
            "requires_expiry": "يتطلب تاريخ انتهاء",
            "is_active": "نشط",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "reorder_level": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "maximum_level": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
        }


class WarehouseForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Warehouse
        fields = [
            "name_ar",
            "name_en",
            "code",
            "department",
            "location",
            "warehouse_type",
            "is_active",
        ]
        labels = {
            "name_ar": "اسم المستودع بالعربية",
            "name_en": "اسم المستودع بالإنجليزية",
            "code": "رمز المستودع",
            "department": "القسم",
            "location": "الموقع",
            "warehouse_type": "نوع المستودع",
            "is_active": "نشط",
        }


class StorageLocationForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = StorageLocation
        fields = [
            "warehouse",
            "name_ar",
            "name_en",
            "code",
            "description",
            "is_active",
        ]
        labels = {
            "warehouse": "المستودع",
            "name_ar": "اسم الموقع بالعربية",
            "name_en": "اسم الموقع بالإنجليزية",
            "code": "رمز الموقع",
            "description": "الوصف",
            "is_active": "نشط",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class StockBatchFilterForm(BootstrapMixin, forms.Form):
    item = forms.ModelChoiceField(
        queryset=InventoryItem.objects.filter(is_active=True).order_by("name_ar"),
        required=False,
        label="الصنف",
    )

    warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.filter(is_active=True).order_by("name_ar"),
        required=False,
        label="المستودع",
    )

    batch_number = forms.CharField(
        required=False,
        label="رقم Batch",
    )


class ReceiveStockForm(BootstrapMixin, forms.Form):
    item = forms.ModelChoiceField(
        queryset=InventoryItem.objects.filter(is_active=True).order_by("name_ar"),
        label="الصنف",
    )

    warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.filter(is_active=True).order_by("name_ar"),
        label="المستودع",
    )

    location = forms.ModelChoiceField(
        queryset=StorageLocation.objects.filter(is_active=True).order_by("name_ar"),
        label="موقع التخزين",
    )

    quantity = forms.DecimalField(
        min_value=0.0001,
        decimal_places=4,
        max_digits=18,
        label="الكمية",
    )

    batch_number = forms.CharField(
        required=False,
        label="رقم Batch",
    )

    expiry_date = forms.DateField(
        required=False,
        label="تاريخ الانتهاء",
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    unit_cost = forms.DecimalField(
        min_value=0,
        decimal_places=4,
        max_digits=18,
        initial=0,
        label="تكلفة الوحدة",
    )

    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.filter(is_active=True).order_by("name_ar"),
        required=False,
        label="المورد",
    )

    reason = forms.CharField(
        required=False,
        label="سبب / ملاحظة",
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def clean(self):
        cleaned = super().clean()

        item = cleaned.get("item")
        warehouse = cleaned.get("warehouse")
        location = cleaned.get("location")

        if warehouse and location:
            if location.warehouse_id != warehouse.id:
                self.add_error(
                    "location",
                    "موقع التخزين لا يتبع المستودع المحدد.",
                )

        if item:
            batch_number = (cleaned.get("batch_number") or "").strip()
            expiry_date = cleaned.get("expiry_date")

            if item.requires_batch and not batch_number:
                self.add_error(
                    "batch_number",
                    "هذا الصنف يتطلب رقم Batch.",
                )

            if item.requires_expiry and expiry_date is None:
                self.add_error(
                    "expiry_date",
                    "هذا الصنف يتطلب تاريخ انتهاء.",
                )

        return cleaned


class IssueStockForm(BootstrapMixin, forms.Form):
    batch = forms.ModelChoiceField(
        queryset=StockBatch.objects.filter(
            is_active=True,
            item__is_active=True,
        ).select_related(
            "item",
            "warehouse",
            "location",
        ).order_by("item__name_ar", "batch_number"),
        label="دفعة المخزون",
    )

    quantity = forms.DecimalField(
        min_value=0.0001,
        decimal_places=4,
        max_digits=18,
        label="الكمية",
    )

    reason = forms.CharField(
        required=False,
        label="سبب الصرف",
        widget=forms.Textarea(attrs={"rows": 3}),
    )


class ReturnStockForm(BootstrapMixin, forms.Form):
    batch = forms.ModelChoiceField(
        queryset=StockBatch.objects.filter(
            is_active=True,
            item__is_active=True,
        ).select_related(
            "item",
            "warehouse",
            "location",
        ).order_by("item__name_ar", "batch_number"),
        label="دفعة المخزون",
    )

    quantity = forms.DecimalField(
        min_value=0.0001,
        decimal_places=4,
        max_digits=18,
        label="الكمية",
    )

    reason = forms.CharField(
        required=False,
        label="سبب الإرجاع",
        widget=forms.Textarea(attrs={"rows": 3}),
    )


class AdjustmentStockForm(BootstrapMixin, forms.Form):
    batch = forms.ModelChoiceField(
        queryset=StockBatch.objects.filter(
            is_active=True,
            item__is_active=True,
        ).select_related(
            "item",
            "warehouse",
            "location",
        ).order_by("item__name_ar", "batch_number"),
        label="دفعة المخزون",
    )

    new_quantity = forms.DecimalField(
        min_value=0,
        decimal_places=4,
        max_digits=18,
        label="الكمية الجديدة",
    )

    reason = forms.CharField(
        label="سبب التعديل",
        widget=forms.Textarea(attrs={"rows": 3}),
    )


class TransferStockForm(BootstrapMixin, forms.Form):
    source_warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.filter(is_active=True).order_by("name_ar"),
        label="المستودع المصدر",
    )

    destination_warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.filter(is_active=True).order_by("name_ar"),
        label="المستودع الوجهة",
    )

    batch = forms.ModelChoiceField(
        queryset=StockBatch.objects.filter(
            is_active=True,
            item__is_active=True,
        ).select_related(
            "item",
            "warehouse",
            "location",
        ).order_by("item__name_ar", "batch_number"),
        label="دفعة المخزون",
    )

    quantity = forms.DecimalField(
        min_value=0.0001,
        decimal_places=4,
        max_digits=18,
        label="الكمية",
    )

    def clean(self):
        cleaned = super().clean()

        source = cleaned.get("source_warehouse")
        destination = cleaned.get("destination_warehouse")
        batch = cleaned.get("batch")
        quantity = cleaned.get("quantity")

        if source and destination and source.id == destination.id:
            self.add_error(
                "destination_warehouse",
                "لا يمكن التحويل من المستودع إلى نفسه.",
            )

        if source and batch and batch.warehouse_id != source.id:
            self.add_error(
                "batch",
                "دفعة المخزون لا تتبع المستودع المصدر.",
            )

        if batch and quantity is not None:
            if batch.quantity < quantity:
                self.add_error(
                    "quantity",
                    "الكمية المطلوبة أكبر من الكمية المتاحة.",
                )

        return cleaned


# ============================================================
# PURCHASE
# ============================================================

class PurchaseForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Purchase
        fields = [
            "supplier",
            "warehouse",
            "purchase_date",
        ]
        widgets = {
            "purchase_date": forms.DateInput(
                attrs={"type": "date"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["supplier"].queryset = (
            Supplier.objects
            .filter(is_active=True)
            .order_by("name_ar")
        )

        self.fields["warehouse"].queryset = (
            Warehouse.objects
            .filter(is_active=True)
            .order_by("name_ar")
        )


class PurchaseItemForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = PurchaseItem
        fields = [
            "item",
            "quantity",
            "unit_cost",
        ]

    def __init__(self, *args, **kwargs):
        self.purchase = kwargs.pop("purchase", None)
        super().__init__(*args, **kwargs)

        self.fields["item"].queryset = (
            InventoryItem.objects
            .filter(is_active=True)
            .order_by("name_ar")
        )

    def clean(self):
        cleaned = super().clean()

        quantity = cleaned.get("quantity")
        unit_cost = cleaned.get("unit_cost")

        if quantity is not None and quantity <= 0:
            self.add_error(
                "quantity",
                "الكمية يجب أن تكون أكبر من صفر."
            )

        if unit_cost is not None and unit_cost < 0:
            self.add_error(
                "unit_cost",
                "تكلفة الوحدة لا يمكن أن تكون سالبة."
            )

        return cleaned


class PurchaseReceiveForm(BootstrapMixin, forms.Form):
    quantity = forms.DecimalField(
        min_value=0.0001,
        decimal_places=4,
        max_digits=18,
        label="الكمية المستلمة",
    )

    location = forms.ModelChoiceField(
        queryset=StorageLocation.objects
        .filter(is_active=True)
        .order_by("name_ar"),
        label="موقع التخزين",
    )

    batch_number = forms.CharField(
        required=False,
        label="رقم Batch",
    )

    expiry_date = forms.DateField(
        required=False,
        label="تاريخ الانتهاء",
        widget=forms.DateInput(
            attrs={"type": "date"}
        ),
    )

    def __init__(self, *args, purchase_item=None, **kwargs):
        self.purchase_item = purchase_item
        super().__init__(*args, **kwargs)

        if purchase_item is not None:
            self.fields["location"].queryset = (
                StorageLocation.objects
                .filter(
                    warehouse_id=purchase_item.purchase.warehouse_id,
                    is_active=True,
                )
                .order_by("name_ar")
            )

    def clean(self):
        cleaned = super().clean()

        if self.purchase_item is None:
            return cleaned

        quantity = cleaned.get("quantity")

        remaining = (
            self.purchase_item.quantity
            - self.purchase_item.received_quantity
        )

        if quantity is not None and quantity > remaining:
            self.add_error(
                "quantity",
                f"الكمية المتبقية هي {remaining} فقط."
            )

        item = self.purchase_item.item

        batch_number = (
            cleaned.get("batch_number") or ""
        ).strip()

        expiry_date = cleaned.get("expiry_date")

        if item.requires_batch and not batch_number:
            self.add_error(
                "batch_number",
                "هذا الصنف يتطلب رقم Batch."
            )

        if item.requires_expiry and expiry_date is None:
            self.add_error(
                "expiry_date",
                "هذا الصنف يتطلب تاريخ انتهاء."
            )

        return cleaned
