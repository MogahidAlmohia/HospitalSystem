from django.conf import settings
from django.db import models

class Notification(models.Model):
    LEVELS = [
        ("INFO", "معلومة"),
        ("SUCCESS", "نجاح"),
        ("WARNING", "تنبيه"),
        ("DANGER", "عاجل"),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    source_key = models.CharField(max_length=120)
    title = models.CharField(max_length=200)
    message = models.TextField()
    url = models.CharField(max_length=500, blank=True)
    level = models.CharField(max_length=20, choices=LEVELS, default="INFO")
    is_read = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_read", "-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "source_key"], name="notification_user_source_unique"),
        ]
        indexes = [
            models.Index(fields=["user", "is_read", "is_active"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.title}"
