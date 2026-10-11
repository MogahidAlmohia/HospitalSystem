from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from patients.models import Patient


class RegisterPatientViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="reception-test",
            password="test-password-123",
        )
        self.client.force_login(self.user)

    def test_register_patient_creates_patient(self):
        response = self.client.post(
            reverse("reception:register_patient"),
            {
                "patient_number": "P-TEST-001",
                "full_name": "مريض اختبار",
                "gender": "M",
                "age": "35",
                "phone": "0500000000",
                "blood_group": "O+",
            },
        )

        self.assertRedirects(response, reverse("reception:dashboard"))
        patient = Patient.objects.get(patient_number="P-TEST-001")
        self.assertEqual(patient.full_name, "مريض اختبار")
        self.assertEqual(patient.age, 35)
        self.assertEqual(patient.gender, "M")

    def test_invalid_age_does_not_create_patient(self):
        response = self.client.post(
            reverse("reception:register_patient"),
            {
                "patient_number": "P-TEST-002",
                "full_name": "مريض اختبار",
                "gender": "M",
                "age": "151",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Patient.objects.filter(patient_number="P-TEST-002").exists())

    def test_invalid_gender_does_not_create_patient(self):
        response = self.client.post(
            reverse("reception:register_patient"),
            {
                "patient_number": "P-TEST-003",
                "full_name": "مريض اختبار",
                "gender": "INVALID",
                "age": "30",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Patient.objects.filter(patient_number="P-TEST-003").exists())
