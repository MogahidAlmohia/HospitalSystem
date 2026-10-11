from .services import sync_system_notifications
from .models import Notification

def notifications(request):
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {"notification_count": 0, "notifications_list": []}
    try:
        sync_system_notifications(request.user)
        qs = Notification.objects.filter(user=request.user, is_active=True)
        return {"notification_count": qs.filter(is_read=False).count(), "notifications_list": qs[:8]}
    except Exception:
        return {"notification_count": 0, "notifications_list": []}
