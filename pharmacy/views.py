from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction, models
from django.db.models import Q, Sum
from decimal import Decimal, InvalidOperation
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from patients.models import Patient
from .forms import MedicineForm, PrescriptionForm, PrescriptionItemForm
from .models import (
    Medicine,
    Prescription,
    PrescriptionItem,
    PharmacyStockMovement,
)


@login_required
def dashboard(request):
    today = timezone.localdate()

    medicines = Medicine.objects.filter(is_active=True)

    prescriptions = Prescription.objects.select_related(
        "patient",
        "doctor",
        "department",
    )

    stock_movements = PharmacyStockMovement.objects.select_related(
        "medicine",
        "created_by",
    )

    total_stock_value = medicines.aggregate(
        total=Sum(
            models.F("stock_quantity") * models.F("price")
        )
    )["total"] or Decimal("0")

    context = {
        "today": today,

        # Medicines / stock
        "total_medicines": medicines.count(),
        "low_stock": medicines.filter(
            stock_quantity__lte=models.F("reorder_level"),
            stock_quantity__gt=0,
        ).count(),
        "out_of_stock": medicines.filter(
            stock_quantity__lte=0
        ).count(),
        "total_stock_quantity": medicines.aggregate(
            total=Sum("stock_quantity")
        )["total"] or Decimal("0"),
        "total_stock_value": total_stock_value,

        # Prescriptions
        "total_prescriptions": prescriptions.count(),
        "today_prescriptions": prescriptions.filter(
            created_at__date=today
        ).count(),
        "pending_prescriptions": prescriptions.filter(
            status="PENDING"
        ).count(),
        "dispensed_prescriptions": prescriptions.filter(
            status="DISPENSED"
        ).count(),
        "cancelled_prescriptions": prescriptions.filter(
            status="CANCELLED"
        ).count(),

        # Recent data
        "recent_prescriptions": prescriptions.order_by(
            "-created_at"
        )[:10],
        "recent_stock_movements": stock_movements.order_by(
            "-created_at"
        )[:10],

        # Alert lists
        "low_stock_medicines": medicines.filter(
            stock_quantity__lte=models.F("reorder_level"),
            stock_quantity__gt=0,
        ).order_by(
            "stock_quantity",
            "name_ar",
        )[:8],
        "out_of_stock_medicines": medicines.filter(
            stock_quantity__lte=0
        ).order_by("name_ar")[:8],
    }

    return render(request, "pharmacy/dashboard.html", context)


@login_required
def medicine_list(request):
    q = request.GET.get("q", "").strip()

    medicines = Medicine.objects.all()

    if q:
        medicines = medicines.filter(
            Q(name_ar__icontains=q)
            | Q(name_en__icontains=q)
            | Q(generic_name__icontains=q)
            | Q(code__icontains=q)
        )

    return render(
        request,
        "pharmacy/medicine_list.html",
        {
            "medicines": medicines,
            "q": q,
        },
    )


@login_required
def medicine_create(request):
    if request.method == "POST":
        form = MedicineForm(request.POST)

        if form.is_valid():
            medicine = form.save()

            messages.success(
                request,
                f"تمت إضافة الدواء {medicine.name_ar} بنجاح."
            )

            return redirect("pharmacy:medicine_list")
    else:
        form = MedicineForm()

    return render(
        request,
        "pharmacy/medicine_form.html",
        {
            "form": form,
            "title": "إضافة دواء",
        },
    )


@login_required
def medicine_update(request, medicine_id):
    medicine = get_object_or_404(Medicine, id=medicine_id)

    if request.method == "POST":
        form = MedicineForm(request.POST, instance=medicine)

        if form.is_valid():
            medicine = form.save()

            messages.success(
                request,
                f"تم تحديث الدواء {medicine.name_ar}."
            )

            return redirect("pharmacy:medicine_list")
    else:
        form = MedicineForm(instance=medicine)

    return render(
        request,
        "pharmacy/medicine_form.html",
        {
            "form": form,
            "title": "تعديل دواء",
            "medicine": medicine,
        },
    )


@login_required
def prescription_list(request):
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()

    prescriptions = Prescription.objects.select_related(
        "patient",
        "doctor",
        "department",
    )

    if q:
        prescriptions = prescriptions.filter(
            Q(prescription_number__icontains=q)
            | Q(patient__full_name__icontains=q)
            | Q(patient__patient_number__icontains=q)
        )

    if status:
        prescriptions = prescriptions.filter(status=status)

    return render(
        request,
        "pharmacy/prescription_list.html",
        {
            "prescriptions": prescriptions,
            "q": q,
            "status": status,
            "status_choices": Prescription.STATUS_CHOICES,
        },
    )


@login_required
def prescription_create(request):
    if request.method == "POST":
        form = PrescriptionForm(request.POST)

        if form.is_valid():
            prescription = form.save(commit=False)
            prescription.prescribed_by = request.user
            prescription.status = "PENDING"
            prescription.save()

            messages.success(
                request,
                f"تم إنشاء الوصفة {prescription.prescription_number}."
            )

            return redirect(
                "pharmacy:prescription_detail",
                prescription_id=prescription.id,
            )
    else:
        form = PrescriptionForm()

    return render(
        request,
        "pharmacy/prescription_form.html",
        {
            "form": form,
            "title": "إنشاء وصفة طبية",
        },
    )


@login_required
def prescription_detail(request, prescription_id):
    prescription = get_object_or_404(
        Prescription.objects.select_related(
            "patient",
            "doctor",
            "department",
            "prescribed_by",
            "dispensed_by",
        ).prefetch_related("items__medicine"),
        id=prescription_id,
    )

    item_form = PrescriptionItemForm()

    return render(
        request,
        "pharmacy/prescription_detail.html",
        {
            "prescription": prescription,
            "item_form": item_form,
        },
    )


@login_required
def prescription_add_item(request, prescription_id):
    prescription = get_object_or_404(
        Prescription,
        id=prescription_id,
    )

    if prescription.status in ["DISPENSED", "CANCELLED"]:
        messages.error(
            request,
            "لا يمكن إضافة دواء إلى وصفة مصروفة أو ملغاة."
        )
        return redirect(
            "pharmacy:prescription_detail",
            prescription_id=prescription.id,
        )

    if request.method == "POST":
        form = PrescriptionItemForm(request.POST)

        if form.is_valid():
            item = form.save(commit=False)
            item.prescription = prescription
            item.save()

            messages.success(
                request,
                f"تمت إضافة {item.medicine.name_ar} إلى الوصفة."
            )

    return redirect(
        "pharmacy:prescription_detail",
        prescription_id=prescription.id,
    )


@login_required
@transaction.atomic
def prescription_dispense(request, prescription_id):
    prescription = get_object_or_404(
        Prescription.objects.select_for_update(),
        id=prescription_id,
    )

    if request.method != "POST":
        return redirect(
            "pharmacy:prescription_detail",
            prescription_id=prescription.id,
        )

    if prescription.status in ["DISPENSED", "CANCELLED"]:
        messages.error(request, "لا يمكن صرف هذه الوصفة.")
        return redirect(
            "pharmacy:prescription_detail",
            prescription_id=prescription.id,
        )

    items = list(
        prescription.items.select_related("medicine").select_for_update()
    )

    if not items:
        messages.error(request, "لا يمكن صرف وصفة بدون أدوية.")
        return redirect(
            "pharmacy:prescription_detail",
            prescription_id=prescription.id,
        )

    for item in items:
        remaining = item.quantity - item.dispensed_quantity

        if remaining <= 0:
            continue

        if item.medicine.stock_quantity < remaining:
            messages.error(
                request,
                f"المخزون غير كافٍ للدواء: {item.medicine.name_ar}"
            )
            return redirect(
                "pharmacy:prescription_detail",
                prescription_id=prescription.id,
            )

    for item in items:
        remaining = item.quantity - item.dispensed_quantity

        if remaining <= 0:
            continue

        medicine = item.medicine

        medicine.stock_quantity -= remaining
        medicine.save(
            update_fields=[
                "stock_quantity",
                "updated_at",
            ]
        )

        item.dispensed_quantity += remaining
        item.save(update_fields=["dispensed_quantity"])

        PharmacyStockMovement.objects.create(
            medicine=medicine,
            movement_type="OUT",
            quantity=remaining,
            balance_after=medicine.stock_quantity,
            reference=prescription.prescription_number,
            notes="صرف وصفة طبية",
            created_by=request.user,
        )

    prescription.status = "DISPENSED"
    prescription.dispensed_by = request.user
    prescription.dispensed_at = timezone.now()
    prescription.save(
        update_fields=[
            "status",
            "dispensed_by",
            "dispensed_at",
            "updated_at",
        ]
    )

    messages.success(
        request,
        f"تم صرف الوصفة {prescription.prescription_number} بنجاح."
    )

    return redirect(
        "pharmacy:prescription_detail",
        prescription_id=prescription.id,
    )


@login_required
def stock_list(request):
    medicines = Medicine.objects.filter(is_active=True)

    return render(
        request,
        "pharmacy/stock_list.html",
        {
            "medicines": medicines,
        },
    )


@login_required
def stock_movements(request):
    movements = PharmacyStockMovement.objects.select_related(
        "medicine",
        "created_by",
    )[:200]

    return render(
        request,
        "pharmacy/stock_movements.html",
        {
            "movements": movements,
        },
    )


@login_required
def patient_prescriptions(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)

    prescriptions = Prescription.objects.filter(
        patient=patient
    ).select_related(
        "doctor",
        "department",
    )

    return render(
        request,
        "pharmacy/prescription_list.html",
        {
            "prescriptions": prescriptions,
            "patient": patient,
            "q": "",
            "status": "",
            "status_choices": Prescription.STATUS_CHOICES,
        },
    )


@login_required
@transaction.atomic
def stock_receive(request, medicine_id):
    medicine = get_object_or_404(
        Medicine.objects.select_for_update(),
        id=medicine_id,
    )

    if request.method == "POST":
        quantity = request.POST.get("quantity", "").strip()
        reference = request.POST.get("reference", "").strip()
        notes = request.POST.get("notes", "").strip()

        try:
            quantity = Decimal(quantity)
        except (InvalidOperation, TypeError, ValueError):
            quantity = Decimal("0")

        if quantity <= 0:
            messages.error(request, "يجب إدخال كمية أكبر من صفر.")
            return redirect("pharmacy:stock_receive", medicine_id=medicine.id)

        medicine.stock_quantity += quantity
        medicine.save(update_fields=["stock_quantity", "updated_at"])

        PharmacyStockMovement.objects.create(
            medicine=medicine,
            movement_type="IN",
            quantity=quantity,
            balance_after=medicine.stock_quantity,
            reference=reference,
            notes=notes or "إدخال مخزون",
            created_by=request.user,
        )

        messages.success(
            request,
            f"تم إدخال {quantity} من {medicine.name_ar} بنجاح."
        )

        return redirect("pharmacy:stock_list")

    return render(
        request,
        "pharmacy/stock_receive.html",
        {"medicine": medicine},
    )


@login_required
@transaction.atomic
def stock_adjust(request, medicine_id):
    medicine = get_object_or_404(
        Medicine.objects.select_for_update(),
        id=medicine_id,
    )

    if request.method == "POST":
        new_quantity = request.POST.get("new_quantity", "").strip()
        reference = request.POST.get("reference", "").strip()
        notes = request.POST.get("notes", "").strip()

        try:
            new_quantity = Decimal(new_quantity)
        except (InvalidOperation, TypeError, ValueError):
            new_quantity = Decimal("-1")

        if new_quantity < 0:
            messages.error(request, "الكمية الجديدة لا يمكن أن تكون سالبة.")
            return redirect("pharmacy:stock_adjust", medicine_id=medicine.id)

        old_quantity = medicine.stock_quantity
        difference = new_quantity - old_quantity

        if difference == 0:
            messages.warning(request, "لا يوجد فرق بين الرصيد الحالي والجديد.")
            return redirect("pharmacy:stock_list")

        medicine.stock_quantity = new_quantity
        medicine.save(update_fields=["stock_quantity", "updated_at"])

        PharmacyStockMovement.objects.create(
            medicine=medicine,
            movement_type="ADJUSTMENT",
            quantity=abs(difference),
            balance_after=medicine.stock_quantity,
            reference=reference,
            notes=(
                notes
                or f"تسوية مخزون: من {old_quantity} إلى {new_quantity}"
            ),
            created_by=request.user,
        )

        messages.success(
            request,
            f"تمت تسوية مخزون {medicine.name_ar} من "
            f"{old_quantity} إلى {new_quantity}."
        )

        return redirect("pharmacy:stock_list")

    return render(
        request,
        "pharmacy/stock_adjust.html",
        {"medicine": medicine},
    )
