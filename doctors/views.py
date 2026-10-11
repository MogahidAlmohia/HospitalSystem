from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from departments.models import Department
from .models import Doctor


User = get_user_model()


@login_required
def doctor_list(request):
    query = request.GET.get("q", "").strip()
    department_id = request.GET.get("department", "").strip()

    doctors = Doctor.objects.select_related(
        "user", "department"
    ).order_by("full_name")

    if query:
        doctors = doctors.filter(
            full_name__icontains=query
        ) | Doctor.objects.select_related(
            "user", "department"
        ).filter(
            doctor_number__icontains=query
        )

    if department_id:
        doctors = doctors.filter(department_id=department_id)

    departments = Department.objects.filter(
        is_active=True
    ).order_by("name_ar")

    context = {
        "doctors": doctors,
        "departments": departments,
        "query": query,
        "department_id": department_id,
        "total_doctors": Doctor.objects.count(),
        "active_doctors": Doctor.objects.filter(is_active=True).count(),
        "inactive_doctors": Doctor.objects.filter(is_active=False).count(),
    }

    return render(
        request,
        "doctors/doctor_list.html",
        context
    )


@login_required
def doctor_create(request):
    departments = Department.objects.filter(
        is_active=True
    ).order_by("name_ar")

    used_user_ids = Doctor.objects.values_list(
        "user_id",
        flat=True
    )

    users = User.objects.filter(
        is_active=True
    ).exclude(
        id__in=used_user_ids
    ).order_by("username")

    if request.method == "POST":
        doctor_number = request.POST.get(
            "doctor_number", ""
        ).strip()

        full_name = request.POST.get(
            "full_name", ""
        ).strip()

        specialty = request.POST.get(
            "specialty", ""
        ).strip()

        department_id = request.POST.get(
            "department", ""
        ).strip()

        phone = request.POST.get(
            "phone", ""
        ).strip()

        license_number = request.POST.get(
            "license_number", ""
        ).strip()

        user_id = request.POST.get(
            "user", ""
        ).strip()

        is_active = request.POST.get("is_active") == "on"

        if not doctor_number:
            messages.error(request, "يجب إدخال رقم الطبيب.")
            return redirect("doctors:create")

        if not full_name:
            messages.error(request, "يجب إدخال اسم الطبيب.")
            return redirect("doctors:create")

        if not department_id:
            messages.error(request, "يجب اختيار القسم.")
            return redirect("doctors:create")

        if not user_id:
            messages.error(
                request,
                "يجب اختيار حساب المستخدم المرتبط بالطبيب."
            )
            return redirect("doctors:create")

        if Doctor.objects.filter(
            doctor_number=doctor_number
        ).exists():
            messages.error(
                request,
                "رقم الطبيب مستخدم مسبقًا."
            )
            return redirect("doctors:create")

        if Doctor.objects.filter(
            user_id=user_id
        ).exists():
            messages.error(
                request,
                "حساب المستخدم مرتبط بطبيب آخر."
            )
            return redirect("doctors:create")

        department = get_object_or_404(
            Department,
            id=department_id,
            is_active=True
        )

        user = get_object_or_404(
            User,
            id=user_id,
            is_active=True
        )

        Doctor.objects.create(
            user=user,
            doctor_number=doctor_number,
            full_name=full_name,
            specialty=specialty,
            department=department,
            phone=phone,
            license_number=license_number,
            is_active=is_active,
        )

        messages.success(
            request,
            "تمت إضافة الطبيب وربطه بالقسم بنجاح."
        )

        return redirect("doctors:list")

    return render(
        request,
        "doctors/doctor_form.html",
        {
            "departments": departments,
            "users": users,
            "doctor": None,
        }
    )


@login_required
def doctor_edit(request, doctor_id):
    doctor = get_object_or_404(
        Doctor,
        id=doctor_id
    )

    departments = Department.objects.filter(
        is_active=True
    ).order_by("name_ar")

    users = User.objects.filter(
        is_active=True
    ).filter(
        id=doctor.user_id
    ) | User.objects.filter(
        is_active=True
    ).exclude(
        id__in=Doctor.objects.exclude(
            id=doctor.id
        ).values_list("user_id", flat=True)
    )

    users = users.distinct().order_by("username")

    if request.method == "POST":
        doctor_number = request.POST.get(
            "doctor_number", ""
        ).strip()

        full_name = request.POST.get(
            "full_name", ""
        ).strip()

        specialty = request.POST.get(
            "specialty", ""
        ).strip()

        department_id = request.POST.get(
            "department", ""
        ).strip()

        phone = request.POST.get(
            "phone", ""
        ).strip()

        license_number = request.POST.get(
            "license_number", ""
        ).strip()

        user_id = request.POST.get(
            "user", ""
        ).strip()

        is_active = request.POST.get("is_active") == "on"

        if not doctor_number or not full_name:
            messages.error(
                request,
                "رقم الطبيب والاسم مطلوبان."
            )
            return redirect(
                "doctors:edit",
                doctor_id=doctor.id
            )

        if not department_id:
            messages.error(
                request,
                "يجب اختيار القسم."
            )
            return redirect(
                "doctors:edit",
                doctor_id=doctor.id
            )

        if not user_id:
            messages.error(
                request,
                "يجب اختيار حساب المستخدم."
            )
            return redirect(
                "doctors:edit",
                doctor_id=doctor.id
            )

        if Doctor.objects.filter(
            doctor_number=doctor_number
        ).exclude(
            id=doctor.id
        ).exists():
            messages.error(
                request,
                "رقم الطبيب مستخدم مسبقًا."
            )
            return redirect(
                "doctors:edit",
                doctor_id=doctor.id
            )

        if Doctor.objects.filter(
            user_id=user_id
        ).exclude(
            id=doctor.id
        ).exists():
            messages.error(
                request,
                "حساب المستخدم مرتبط بطبيب آخر."
            )
            return redirect(
                "doctors:edit",
                doctor_id=doctor.id
            )

        doctor.doctor_number = doctor_number
        doctor.full_name = full_name
        doctor.specialty = specialty
        doctor.department = get_object_or_404(
            Department,
            id=department_id,
            is_active=True
        )
        doctor.phone = phone
        doctor.license_number = license_number
        doctor.user = get_object_or_404(
            User,
            id=user_id,
            is_active=True
        )
        doctor.is_active = is_active
        doctor.save()

        messages.success(
            request,
            "تم تحديث بيانات الطبيب بنجاح."
        )

        return redirect("doctors:list")

    return render(
        request,
        "doctors/doctor_form.html",
        {
            "departments": departments,
            "users": users,
            "doctor": doctor,
        }
    )


@login_required
def doctor_toggle(request, doctor_id):
    doctor = get_object_or_404(
        Doctor,
        id=doctor_id
    )

    doctor.is_active = not doctor.is_active
    doctor.save(update_fields=["is_active", "updated_at"])

    if doctor.is_active:
        messages.success(
            request,
            "تم تفعيل الطبيب."
        )
    else:
        messages.warning(
            request,
            "تم تعطيل الطبيب."
        )

    return redirect("doctors:list")
