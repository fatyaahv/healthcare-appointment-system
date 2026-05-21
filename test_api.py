import unittest
from http import HTTPStatus

from api_server import AppointmentApi, AppointmentRepository
from external_service import HolidayService


class StubHolidayService(HolidayService):
    def get_public_holidays(self, year: int, country_code: str = "TR"):
        return {
            "source": "test stub",
            "year": year,
            "countryCode": country_code,
            "holidays": [{"date": f"{year}-01-01", "localName": "Yilbasi", "name": "New Year's Day"}],
        }


class AppointmentApiTests(unittest.TestCase):
    def setUp(self):
        self.api = AppointmentApi(AppointmentRepository(), StubHolidayService())

    def test_lists_all_appointments_from_xml(self):
        status, payload = self.api.handle("GET", "/api/appointments", {})

        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(len(payload["appointments"]), 25)
        self.assertEqual(payload["appointments"][0]["appointmentId"], "A01")

    def test_filters_appointments_by_status_and_doctor(self):
        status, payload = self.api.handle(
            "GET",
            "/api/appointments",
            {"status": ["Pending"], "doctorId": ["D01"]},
        )

        self.assertEqual(status, HTTPStatus.OK)
        self.assertTrue(payload["appointments"])
        self.assertTrue(all(item["status"] == "Pending" for item in payload["appointments"]))
        self.assertTrue(all(item["doctorId"] == "D01" for item in payload["appointments"]))

    def test_returns_not_found_for_unknown_appointment(self):
        status, payload = self.api.handle("GET", "/api/appointments/A99", {})

        self.assertEqual(status, HTTPStatus.NOT_FOUND)
        self.assertIn("not found", payload["error"].lower())

    def test_rejects_invalid_status_filter(self):
        status, payload = self.api.handle("GET", "/api/appointments", {"status": ["Delayed"]})

        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertIn("status", payload["error"])

    def test_summary_report_matches_xml_dataset(self):
        status, payload = self.api.handle("GET", "/api/reports/summary", {})

        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(payload["totalAppointments"], 25)
        self.assertEqual(payload["totalDoctors"], 5)
        self.assertEqual(payload["totalPatients"], 15)

    def test_external_holiday_integration_endpoint(self):
        status, payload = self.api.handle(
            "GET",
            "/api/integration/holidays",
            {"year": ["2026"], "countryCode": ["TR"]},
        )

        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(payload["source"], "test stub")
        self.assertEqual(payload["holidays"][0]["date"], "2026-01-01")


if __name__ == "__main__":
    unittest.main()
