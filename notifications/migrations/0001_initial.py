from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="Notification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_key", models.CharField(max_length=120)),
                ("title", models.CharField(max_length=200)),
                ("message", models.TextField()),
                ("url", models.CharField(blank=True, max_length=500)),
                ("level", models.CharField(choices=[("INFO", "معلومة"), ("SUCCESS", "نجاح"), ("WARNING", "تنبيه"), ("DANGER", "عاجل")], default="INFO", max_length=20)),
                ("is_read", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-is_read", "-created_at"]},
        ),
        migrations.AddConstraint(
            model_name="notification",
            constraint=models.UniqueConstraint(fields=("user", "source_key"), name="notification_user_source_unique"),
        ),
        migrations.AddIndex(model_name="notification", index=models.Index(fields=["user", "is_read", "is_active"], name="notificatio_user_id_9a9e42_idx")),
        migrations.AddIndex(model_name="notification", index=models.Index(fields=["created_at"], name="notificatio_created_8e2a15_idx")),
    ]
