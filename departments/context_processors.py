from .models import Department


def sidebar_departments(request):
    if not request.user.is_authenticated:
        return {"sidebar_departments": []}

    departments = Department.objects.filter(
        is_active=True,
        department_type="CLINICAL",
    ).order_by("name_ar")

    return {
        "sidebar_departments": departments,
    }
