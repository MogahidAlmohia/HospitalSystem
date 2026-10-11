from django.conf import settings
from django.conf.urls.static import static
"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from django.shortcuts import redirect


def home(request):
    if not request.user.is_authenticated:
        return redirect("accounts:login")
    return redirect("accounts:dashboard")


urlpatterns = [
    path("notifications/", include("notifications.urls")),
    path("reports/", include("reports.urls")),
    path("system-settings/", include("system_settings.urls")),
    path("emergency/", include("emergency.urls")),
    path("inpatient/", include("inpatient.urls")),
    path("departments/", include("departments.urls")),
    path("patients/", include("patients.urls")),
    path("doctors/", include("doctors.urls")),
    path("radiology/", include("radiology.urls")),
    path("pharmacy/", include("pharmacy.urls")),
    path("billing/", include("billing.urls")),
    path("inventory/", include("inventory.urls")),
    path("blood-bank/", include("blood_bank.urls")),
    path("nursing/", include("nursing.urls")),
    path("surgery/", include("surgery.urls")),
    # الصفحة الرئيسية
    path("", home, name="home"),

    # الحسابات وتسجيل الدخول
    path(
        "accounts/",
        include("accounts.urls")
    ),

    # الاستقبال
    path(
        "reception/",
        include("reception.urls")
    ),

    # المختبر
    path(
        "laboratory/",
        include("laboratory.urls")
    ),
]

    
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
