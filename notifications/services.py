from django.db import models
from django.urls import reverse

from .models import Notification

def _set_notification(user, key, title, message, url, level, active=True):
    obj, _ = Notification.objects.get_or_create(
        user=user, source_key=key,
        defaults={"title": title, "message": message, "url": url, "level": level, "is_active": active},
    )
    changed = []
    for field, value in (("title", title), ("message", message), ("url", url), ("level", level), ("is_active", active)):
        if getattr(obj, field) != value:
            setattr(obj, field, value); changed.append(field)
    if changed:
        obj.save(update_fields=changed + ["updated_at"])
    return obj

def sync_system_notifications(user):
    if not user.is_authenticated:
        return
    try:
        from accounts.permissions import get_user_role
        role = get_user_role(user)
    except Exception:
        role = "OTHER"
    manager = role in {"ADMIN", "MANAGER"} or user.is_superuser
    sources = set()

    try:
        from laboratory.models import LaboratoryOrder, LaboratoryOrderItem
        urgent = LaboratoryOrder.objects.filter(priority__in=["URGENT", "STAT"]).exclude(status__in=["COMPLETED", "CANCELLED"]).count()
        if urgent:
            key = "lab.urgent"; sources.add(key)
            if manager or role == "LAB":
                _set_notification(user, key, "طلبات مختبر عاجلة", f"يوجد {urgent} طلب مختبر عاجل أو STAT يحتاج متابعة.", reverse("laboratory:result_workflow_dashboard"), "DANGER")
        pending_verify = LaboratoryOrderItem.objects.filter(status="COMPLETED", verified=False).count()
        if pending_verify:
            key = "lab.verify"; sources.add(key)
            if manager or role == "LAB" or role == "DOCTOR":
                _set_notification(user, key, "نتائج بانتظار الاعتماد", f"يوجد {pending_verify} نتيجة مكتملة بانتظار الاعتماد.", reverse("laboratory:result_workflow_dashboard"), "WARNING")
        critical = LaboratoryOrderItem.objects.filter(critical_status__in=["CRITICAL_LOW", "CRITICAL_HIGH"]).count()
        if critical:
            key = "lab.critical"; sources.add(key)
            if manager or role in {"LAB", "DOCTOR"}:
                _set_notification(user, key, "نتائج حرجة", f"يوجد {critical} نتيجة تحمل حالة حرجة وتحتاج مراجعة.", reverse("laboratory:result_workflow_dashboard"), "DANGER")
    except Exception:
        pass

    try:
        from emergency.models import EmergencyCase
        emergency = EmergencyCase.objects.filter(status__in=["WAITING", "TRIAGE", "UNDER_CARE", "OBSERVATION"], triage_level__in=["RED", "ORANGE"]).count()
        if emergency:
            key = "emergency.urgent"; sources.add(key)
            if manager or role == "EMERGENCY":
                _set_notification(user, key, "حالات طوارئ عالية الأولوية", f"يوجد {emergency} حالة طوارئ بمستوى أحمر/برتقالي.", reverse("emergency:dashboard"), "DANGER")
    except Exception:
        pass

    try:
        from inpatient.models import Bed
        available = Bed.objects.filter(status="AVAILABLE").count()
        if available == 0:
            key = "inpatient.no_beds"; sources.add(key)
            if manager or role == "INPATIENT":
                _set_notification(user, key, "لا توجد أسرة متاحة", "لا يوجد حالياً سرير متاح للتنويم.", reverse("inpatient:bed_list"), "WARNING")
    except Exception:
        pass

    if manager:
        try:
            from inventory.models import StockBatch
            low = StockBatch.objects.filter(is_active=True).filter(quantity__lte=models.F("item__reorder_level")).values("item").distinct().count()
        except Exception:
            low = 0
        if low:
            key = "inventory.low_stock"; sources.add(key)
            _set_notification(user, key, "مخزون منخفض", f"يوجد {low} صنفاً عند أو دون حد إعادة الطلب.", reverse("inventory:dashboard"), "WARNING")

    # تعطيل التنبيهات الآلية التي لم تعد حالتها قائمة، مع إبقاء سجل القراءة.
    if sources:
        Notification.objects.filter(user=user, source_key__startswith="lab.").exclude(source_key__in=sources).update(is_active=False)
        Notification.objects.filter(user=user, source_key__startswith="emergency.").exclude(source_key__in=sources).update(is_active=False)
        Notification.objects.filter(user=user, source_key__startswith="inpatient.").exclude(source_key__in=sources).update(is_active=False)
        Notification.objects.filter(user=user, source_key__startswith="inventory.").exclude(source_key__in=sources).update(is_active=False)
