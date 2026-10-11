from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from .models import Notification

@login_required
def notification_list(request):
    qs = Notification.objects.filter(user=request.user, is_active=True)
    return render(request, "notifications/list.html", {"notifications": qs})

@login_required
def mark_read(request, notification_id):
    n = get_object_or_404(Notification, id=notification_id, user=request.user)
    if request.method == "POST":
        n.is_read = True
        n.save(update_fields=["is_read", "updated_at"])
        if n.url:
            return redirect(n.url)
    return redirect("notifications:list")

@login_required
def mark_all_read(request):
    if request.method == "POST":
        Notification.objects.filter(user=request.user, is_active=True, is_read=False).update(is_read=True)
    return redirect("notifications:list")
