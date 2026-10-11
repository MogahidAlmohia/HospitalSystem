from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.permissions import get_user_role
from patients.models import Patient, Visit

from .forms import BillForm, BillItemForm, BillPaymentForm
from .models import Bill, BillItem, BillPayment


@login_required
def dashboard(request):
    role = get_user_role(request.user)
    today = timezone.localdate()

    context = {
        "role": role,
        "today": today,
        "total_bills": Bill.objects.count(),
        "today_bills": Bill.objects.filter(
            created_at__date=today
        ).count(),
        "draft_bills": Bill.objects.filter(
            status="DRAFT"
        ).count(),
        "issued_bills": Bill.objects.filter(
            status="ISSUED"
        ).count(),
        "partial_bills": Bill.objects.filter(
            status="PARTIAL"
        ).count(),
        "paid_bills": Bill.objects.filter(
            status="PAID"
        ).count(),
        "cancelled_bills": Bill.objects.filter(
            status="CANCELLED"
        ).count(),
        "today_revenue": BillPayment.objects.filter(
            paid_at__date=today
        ).aggregate(
            total=Sum("amount")
        )["total"] or Decimal("0.00"),
        "recent_bills": Bill.objects.select_related(
            "patient"
        ).prefetch_related("items").order_by("-created_at")[:10],
    }

    return render(
        request,
        "billing/dashboard.html",
        context,
    )


@login_required
def bill_list(request):
    bills = Bill.objects.select_related(
        "patient",
        "visit",
        "created_by",
    ).order_by("-created_at")

    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()

    if query:
        bills = bills.filter(
            Q(bill_number__icontains=query)
            | Q(patient__full_name__icontains=query)
            | Q(patient__patient_number__icontains=query)
            | Q(patient__phone__icontains=query)
        )

    if status:
        bills = bills.filter(status=status)

    context = {
        "bills": bills,
        "query": query,
        "status": status,
        "status_choices": Bill.STATUS_CHOICES,
    }

    return render(
        request,
        "billing/bill_list.html",
        context,
    )


@login_required
def bill_detail(request, bill_id):
    bill = get_object_or_404(
        Bill.objects.select_related(
            "patient",
            "visit",
            "created_by",
        ).prefetch_related(
            "items",
            "payments",
        ),
        id=bill_id,
    )

    return render(
        request,
        "billing/bill_detail.html",
        {
            "bill": bill,
            "items": bill.items.all(),
            "payments": bill.payments.all(),
        },
    )


@login_required
def bill_create(request):
    if request.method == "POST":
        form = BillForm(request.POST)

        if form.is_valid():
            bill = form.save(commit=False)
            bill.created_by = request.user
            bill.status = "DRAFT"
            bill.paid_amount = Decimal("0.00")
            bill.subtotal = Decimal("0.00")
            bill.total = Decimal("0.00")
            bill.save()

            messages.success(
                request,
                f"تم إنشاء الفاتورة {bill.bill_number} بنجاح.",
            )

            return redirect(
                "billing:bill_detail",
                bill_id=bill.id,
            )
    else:
        form = BillForm()

    return render(
        request,
        "billing/bill_form.html",
        {
            "form": form,
            "title": "إنشاء فاتورة جديدة",
            "submit_text": "إنشاء الفاتورة",
        },
    )


@login_required
def bill_update(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id)

    if bill.status == "PAID":
        messages.warning(
            request,
            "لا يمكن تعديل فاتورة مدفوعة بالكامل.",
        )
        return redirect(
            "billing:bill_detail",
            bill_id=bill.id,
        )

    if request.method == "POST":
        form = BillForm(
            request.POST,
            instance=bill,
        )

        if form.is_valid():
            bill = form.save(commit=False)

            if bill.discount > bill.subtotal:
                messages.error(
                    request,
                    "الخصم لا يمكن أن يتجاوز إجمالي البنود.",
                )
            else:
                bill.calculate_totals()
                bill.save()

                messages.success(
                    request,
                    "تم تحديث الفاتورة بنجاح.",
                )

                return redirect(
                    "billing:bill_detail",
                    bill_id=bill.id,
                )
    else:
        form = BillForm(instance=bill)

    return render(
        request,
        "billing/bill_form.html",
        {
            "form": form,
            "bill": bill,
            "title": f"تعديل الفاتورة {bill.bill_number}",
            "submit_text": "حفظ التعديلات",
        },
    )


@login_required
def bill_item_create(request, bill_id):
    bill = get_object_or_404(
        Bill,
        id=bill_id,
    )

    if bill.status in ["PAID", "CANCELLED"]:
        messages.error(
            request,
            "لا يمكن إضافة بند إلى هذه الفاتورة.",
        )
        return redirect(
            "billing:bill_detail",
            bill_id=bill.id,
        )

    if request.method == "POST":
        form = BillItemForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                item = form.save(commit=False)
                item.bill = bill
                item.save()

                bill.calculate_totals()
                bill.save()

            messages.success(
                request,
                "تمت إضافة بند الفاتورة بنجاح.",
            )

            return redirect(
                "billing:bill_detail",
                bill_id=bill.id,
            )
    else:
        form = BillItemForm()

    return render(
        request,
        "billing/bill_item_form.html",
        {
            "form": form,
            "bill": bill,
            "title": "إضافة بند إلى الفاتورة",
        },
    )


@login_required
def bill_item_delete(request, item_id):
    item = get_object_or_404(
        BillItem.objects.select_related("bill"),
        id=item_id,
    )

    bill = item.bill

    if bill.status in ["PAID", "CANCELLED"]:
        messages.error(
            request,
            "لا يمكن حذف بند من هذه الفاتورة.",
        )
        return redirect(
            "billing:bill_detail",
            bill_id=bill.id,
        )

    if request.method == "POST":
        with transaction.atomic():
            item.delete()
            bill.calculate_totals()
            bill.save()

        messages.success(
            request,
            "تم حذف بند الفاتورة.",
        )

    return redirect(
        "billing:bill_detail",
        bill_id=bill.id,
    )


@login_required
def bill_payment_create(request, bill_id):
    bill = get_object_or_404(
        Bill,
        id=bill_id,
    )

    if bill.status in ["PAID", "CANCELLED"]:
        messages.error(
            request,
            "لا يمكن تسجيل دفعة لهذه الفاتورة.",
        )
        return redirect(
            "billing:bill_detail",
            bill_id=bill.id,
        )

    if bill.remaining_amount <= Decimal("0.00"):
        messages.warning(
            request,
            "لا يوجد مبلغ متبقٍ على هذه الفاتورة.",
        )
        return redirect(
            "billing:bill_detail",
            bill_id=bill.id,
        )

    if request.method == "POST":
        form = BillPaymentForm(
            request.POST,
            bill=bill,
        )

        if form.is_valid():
            with transaction.atomic():
                payment = form.save(commit=False)
                payment.bill = bill
                payment.received_by = request.user
                payment.save()

                bill.paid_amount = bill.payments.aggregate(
                    total=Sum("amount")
                )["total"] or Decimal("0.00")

                bill.calculate_totals()
                bill.save()

            messages.success(
                request,
                f"تم تسجيل الدفعة {payment.amount} بنجاح.",
            )

            return redirect(
                "billing:bill_detail",
                bill_id=bill.id,
            )
    else:
        form = BillPaymentForm(
            bill=bill,
        )

    return render(
        request,
        "billing/payment_form.html",
        {
            "form": form,
            "bill": bill,
            "remaining": bill.remaining_amount,
            "title": "تسجيل دفعة",
        },
    )


@login_required
def bill_status_update(request, bill_id, status):
    bill = get_object_or_404(
        Bill,
        id=bill_id,
    )

    allowed_statuses = {
        "ISSUED",
        "CANCELLED",
    }

    if status not in allowed_statuses:
        messages.error(
            request,
            "حالة الفاتورة غير صحيحة.",
        )
        return redirect(
            "billing:bill_detail",
            bill_id=bill.id,
        )

    if bill.status == "PAID":
        messages.error(
            request,
            "لا يمكن تغيير حالة فاتورة مدفوعة.",
        )
        return redirect(
            "billing:bill_detail",
            bill_id=bill.id,
        )

    if status == "ISSUED":
        if not bill.items.exists():
            messages.error(
                request,
                "لا يمكن إصدار فاتورة بدون بنود.",
            )
            return redirect(
                "billing:bill_detail",
                bill_id=bill.id,
            )

        bill.calculate_totals()

    if status == "CANCELLED":
        bill.status = "CANCELLED"
    else:
        bill.status = "ISSUED"

    bill.save()

    messages.success(
        request,
        "تم تحديث حالة الفاتورة.",
    )

    return redirect(
        "billing:bill_detail",
        bill_id=bill.id,
    )


@login_required
def patient_bills(request, patient_id):
    patient = get_object_or_404(
        Patient,
        id=patient_id,
    )

    bills = Bill.objects.filter(
        patient=patient
    ).select_related(
        "visit",
        "created_by",
    ).order_by("-created_at")

    return render(
        request,
        "billing/patient_bills.html",
        {
            "patient": patient,
            "bills": bills,
        },
    )
