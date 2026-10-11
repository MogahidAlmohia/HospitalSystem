from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from departments.models import Department
from .models import StaffProfile
from .permissions import get_effective_permissions, user_has_access, user_has_permission


class AccountSecurityTests(TestCase):
    def setUp(self):
        self.department = Department.objects.create(
            name_ar="قسم الاختبار",
            name_en="Test Department",
            code="TEST",
        )
        self.user = User.objects.create_user(
            username="doctor1",
            password="Strong-pass-123",
        )
        self.profile = StaffProfile.objects.create(
            user=self.user,
            employee_number="EMP-001",
            full_name="Test Doctor",
            role="DOCTOR",
            department=self.department,
        )

    def test_login_redirects_to_role_landing_page(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "doctor1", "password": "Strong-pass-123"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response["Location"],
            reverse("accounts:dashboard"),
        )
        landing = self.client.get(reverse("accounts:dashboard"), follow=False)
        self.assertEqual(landing.status_code, 302)
        self.assertEqual(
            landing["Location"],
            reverse("departments:dashboard", kwargs={"department_id": self.department.id}),
        )

    def test_denied_permission_overrides_role_permission(self):
        self.profile.denied_permissions = ["patients.view"]
        self.profile.save(update_fields=["denied_permissions"])

        self.assertFalse(user_has_permission(self.user, "patients.view"))
        self.assertNotIn("patients.view", get_effective_permissions(self.user))

    def test_role_access_is_limited_to_allowed_apps(self):
        self.assertTrue(user_has_access(self.user, "patients"))
        self.assertFalse(user_has_access(self.user, "billing"))

    def test_doctor_app_access_boundaries(self):
        self.assertTrue(user_has_access(self.user, "patients"))
        self.assertTrue(user_has_access(self.user, "laboratory"))
        self.assertTrue(user_has_access(self.user, "radiology"))
        self.assertFalse(user_has_access(self.user, "billing"))
        self.assertFalse(user_has_access(self.user, "inventory"))

    def test_doctor_detailed_permission_boundaries(self):
        self.assertTrue(user_has_permission(self.user, "patients.view"))
        self.assertTrue(user_has_permission(self.user, "laboratory.create_order"))
        self.assertTrue(user_has_permission(self.user, "laboratory.orders.view"))
        self.assertTrue(user_has_permission(self.user, "radiology.orders.view"))
        self.assertFalse(user_has_permission(self.user, "billing.view"))
        self.assertFalse(user_has_permission(self.user, "inventory.view"))

    def test_lab_app_access_boundaries(self):
        self.profile.role = "LAB"
        self.profile.save(update_fields=["role"])
        self.assertTrue(user_has_access(self.user, "patients"))
        self.assertTrue(user_has_access(self.user, "laboratory"))
        self.assertFalse(user_has_access(self.user, "billing"))
        self.assertFalse(user_has_access(self.user, "surgery"))
        self.assertFalse(user_has_access(self.user, "radiology"))

    def test_lab_detailed_permissions(self):
        self.profile.role = "LAB"
        self.profile.save(update_fields=["role"])
        self.assertTrue(user_has_permission(self.user, "laboratory.sample.receive"))
        self.assertTrue(user_has_permission(self.user, "laboratory.results.enter"))
        self.assertTrue(user_has_permission(self.user, "laboratory.results.verify"))
        self.assertTrue(user_has_permission(self.user, "laboratory.tests.create"))
        self.assertTrue(user_has_permission(self.user, "laboratory.devices.create"))
        self.assertTrue(user_has_permission(self.user, "laboratory.reagents.create"))
        self.assertTrue(user_has_permission(self.user, "laboratory.inventory.movement"))
        self.assertFalse(user_has_permission(self.user, "billing.view"))
        self.assertFalse(user_has_permission(self.user, "radiology.results.enter"))

    def test_inactive_profile_cannot_access_dashboard(self):
        self.profile.is_active = False
        self.profile.save(update_fields=["is_active"])
        self.client.force_login(self.user)

        response = self.client.get(reverse("accounts:dashboard"))
        self.assertRedirects(response, reverse("accounts:login"))
