from django.test import SimpleTestCase, RequestFactory

from patients.views import _department_id_conflicts


class DepartmentConflictTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_same_department_does_not_conflict(self):
        request = self.factory.post(
            "/patients/create/?department_id=1",
            {"department_id": "1"},
        )
        self.assertFalse(_department_id_conflicts(request))

    def test_different_departments_conflict(self):
        request = self.factory.post(
            "/patients/create/?department_id=1",
            {"department_id": "2"},
        )
        self.assertTrue(_department_id_conflicts(request))

    def test_missing_post_department_does_not_conflict(self):
        request = self.factory.post(
            "/patients/create/?department_id=1",
            {},
        )
        self.assertFalse(_department_id_conflicts(request))

    def test_get_only_does_not_conflict(self):
        request = self.factory.get(
            "/patients/create/?department_id=1",
        )
        self.assertFalse(_department_id_conflicts(request))
