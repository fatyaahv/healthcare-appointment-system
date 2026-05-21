from __future__ import annotations

import json
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse
from xml.etree import ElementTree as ET

from external_service import HolidayService


BASE_DIR = Path(__file__).resolve().parent
XML_FILE = BASE_DIR / "appointments.xml"
NS_URI = "https://www.saglikrandevu.com/schema"
NS = {"h": NS_URI}
ALLOWED_STATUSES = {"Pending", "Completed", "Cancelled"}


def text(parent: ET.Element, query: str) -> str:
    node = parent.find(query, NS)
    return node.text.strip() if node is not None and node.text else ""


class AppointmentRepository:
    def __init__(self, xml_path: Path = XML_FILE) -> None:
        self.xml_path = xml_path
        self._root = self._load_root()

    def _load_root(self) -> ET.Element:
        if not self.xml_path.exists():
            raise FileNotFoundError(f"Missing XML file: {self.xml_path}")
        return ET.parse(self.xml_path).getroot()

    def list_clinics(self) -> list[dict[str, Any]]:
        clinics: list[dict[str, Any]] = []
        for clinic in self._root.findall("h:clinics/h:clinic", NS):
            clinics.append(
                {
                    "clinicId": text(clinic, "h:clinicId"),
                    "clinicName": text(clinic, "h:clinicName"),
                    "doctors": [
                        {
                            "doctorId": text(doctor, "h:doctorId"),
                            "firstName": text(doctor, "h:firstName"),
                            "lastName": text(doctor, "h:lastName"),
                            "email": text(doctor, "h:email"),
                        }
                        for doctor in clinic.findall("h:doctors/h:doctor", NS)
                    ],
                }
            )
        return clinics

    def list_doctors(self) -> list[dict[str, str]]:
        doctors: list[dict[str, str]] = []
        for clinic in self.list_clinics():
            for doctor in clinic["doctors"]:
                doctors.append(
                    {
                        **doctor,
                        "clinicId": clinic["clinicId"],
                        "clinicName": clinic["clinicName"],
                    }
                )
        return doctors

    def list_patients(self) -> list[dict[str, str]]:
        return [
            {
                "patientId": text(patient, "h:patientId"),
                "firstName": text(patient, "h:firstName"),
                "lastName": text(patient, "h:lastName"),
                "phone": text(patient, "h:phone"),
                "email": text(patient, "h:email"),
                "dateOfBirth": text(patient, "h:dateOfBirth"),
            }
            for patient in self._root.findall("h:patients/h:patient", NS)
        ]

    def list_appointments(
        self,
        status: str | None = None,
        doctor_id: str | None = None,
        patient_id: str | None = None,
    ) -> list[dict[str, str]]:
        appointments = []
        for appointment in self._root.findall("h:appointments/h:appointment", NS):
            item = {
                "appointmentId": text(appointment, "h:appointmentId"),
                "doctorId": text(appointment, "h:doctorId"),
                "patientId": text(appointment, "h:patientId"),
                "appointmentDateTime": text(appointment, "h:appointmentDateTime"),
                "status": text(appointment, "h:status"),
                "notes": text(appointment, "h:notes"),
            }
            if status and item["status"].lower() != status.lower():
                continue
            if doctor_id and item["doctorId"].lower() != doctor_id.lower():
                continue
            if patient_id and item["patientId"].lower() != patient_id.lower():
                continue
            appointments.append(item)
        return appointments

    def get_appointment(self, appointment_id: str) -> dict[str, str] | None:
        for appointment in self.list_appointments():
            if appointment["appointmentId"].lower() == appointment_id.lower():
                return appointment
        return None

    def appointment_summary(self) -> dict[str, Any]:
        appointments = self.list_appointments()
        status_counts = {status: 0 for status in sorted(ALLOWED_STATUSES)}
        for appointment in appointments:
            status_counts[appointment["status"]] = status_counts.get(appointment["status"], 0) + 1
        return {
            "totalAppointments": len(appointments),
            "totalClinics": len(self.list_clinics()),
            "totalDoctors": len(self.list_doctors()),
            "totalPatients": len(self.list_patients()),
            "statusCounts": status_counts,
        }


class AppointmentApi:
    def __init__(self, repository: AppointmentRepository, holiday_service: HolidayService) -> None:
        self.repository = repository
        self.holiday_service = holiday_service

    def handle(self, method: str, path: str, query: dict[str, list[str]]) -> tuple[int, dict[str, Any]]:
        if method != "GET":
            return HTTPStatus.METHOD_NOT_ALLOWED, {"error": "Only GET endpoints are supported."}

        if path == "/api/health":
            return HTTPStatus.OK, {"status": "ok", "dataSource": str(self.repository.xml_path.name)}
        if path == "/api/clinics":
            return HTTPStatus.OK, {"clinics": self.repository.list_clinics()}
        if path == "/api/doctors":
            return HTTPStatus.OK, {"doctors": self.repository.list_doctors()}
        if path == "/api/patients":
            return HTTPStatus.OK, {"patients": self.repository.list_patients()}
        if path == "/api/appointments":
            status = first_query_value(query, "status")
            if status and status not in ALLOWED_STATUSES:
                return HTTPStatus.BAD_REQUEST, {"error": f"status must be one of {sorted(ALLOWED_STATUSES)}"}
            appointments = self.repository.list_appointments(
                status=status,
                doctor_id=first_query_value(query, "doctorId"),
                patient_id=first_query_value(query, "patientId"),
            )
            return HTTPStatus.OK, {"appointments": appointments}
        if path.startswith("/api/appointments/"):
            appointment_id = path.rsplit("/", 1)[-1]
            appointment = self.repository.get_appointment(appointment_id)
            if appointment is None:
                return HTTPStatus.NOT_FOUND, {"error": f"Appointment {appointment_id} was not found."}
            return HTTPStatus.OK, {"appointment": appointment}
        if path == "/api/reports/summary":
            return HTTPStatus.OK, self.repository.appointment_summary()
        if path == "/api/integration/holidays":
            year_value = first_query_value(query, "year") or str(datetime.now().year)
            country_code = first_query_value(query, "countryCode") or "TR"
            try:
                year = int(year_value)
            except ValueError:
                return HTTPStatus.BAD_REQUEST, {"error": "year must be a number."}
            return HTTPStatus.OK, self.holiday_service.get_public_holidays(year, country_code)

        return HTTPStatus.NOT_FOUND, {"error": f"No route found for {path}"}


def first_query_value(query: dict[str, list[str]], name: str) -> str | None:
    values = query.get(name)
    return values[0] if values else None


def build_openapi_document() -> dict[str, Any]:
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "Healthcare Appointment System API",
            "version": "1.0.0",
            "description": "REST API that exposes the XML healthcare appointment dataset.",
        },
        "servers": [{"url": "http://localhost:8000"}],
        "paths": {
            "/api/health": {"get": {"summary": "Check API health", "responses": {"200": {"description": "API is running"}}}},
            "/api/clinics": {"get": {"summary": "List clinics and doctors", "responses": {"200": {"description": "Clinics returned"}}}},
            "/api/doctors": {"get": {"summary": "List doctors", "responses": {"200": {"description": "Doctors returned"}}}},
            "/api/patients": {"get": {"summary": "List patients", "responses": {"200": {"description": "Patients returned"}}}},
            "/api/appointments": {
                "get": {
                    "summary": "List appointments",
                    "parameters": [
                        {"name": "status", "in": "query", "schema": {"type": "string", "enum": sorted(ALLOWED_STATUSES)}},
                        {"name": "doctorId", "in": "query", "schema": {"type": "string", "example": "D01"}},
                        {"name": "patientId", "in": "query", "schema": {"type": "string", "example": "P01"}},
                    ],
                    "responses": {"200": {"description": "Appointments returned"}, "400": {"description": "Invalid filter"}},
                }
            },
            "/api/appointments/{appointmentId}": {
                "get": {
                    "summary": "Get appointment by id",
                    "parameters": [{"name": "appointmentId", "in": "path", "required": True, "schema": {"type": "string", "example": "A01"}}],
                    "responses": {"200": {"description": "Appointment returned"}, "404": {"description": "Appointment not found"}},
                }
            },
            "/api/reports/summary": {"get": {"summary": "Get appointment totals", "responses": {"200": {"description": "Summary returned"}}}},
            "/api/integration/holidays": {
                "get": {
                    "summary": "Fetch public holidays from an external service",
                    "parameters": [
                        {"name": "year", "in": "query", "schema": {"type": "integer", "example": 2026}},
                        {"name": "countryCode", "in": "query", "schema": {"type": "string", "example": "TR"}},
                    ],
                    "responses": {"200": {"description": "Holiday data returned"}},
                }
            },
        },
    }


class RequestHandler(BaseHTTPRequestHandler):
    api = AppointmentApi(AppointmentRepository(), HolidayService())

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/docs"}:
            self.send_html(swagger_ui_html())
            return
        if parsed.path == "/openapi.json":
            self.send_json(HTTPStatus.OK, build_openapi_document())
            return

        status, payload = self.api.handle("GET", parsed.path, parse_qs(parsed.query))
        self.send_json(status, payload)

    def send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def swagger_ui_html() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Healthcare Appointment System API</title>
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    window.onload = () => SwaggerUIBundle({ url: "/openapi.json", dom_id: "#swagger-ui" });
  </script>
</body>
</html>"""


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), RequestHandler)
    print(f"API running at http://{host}:{port}")
    print(f"Swagger documentation at http://{host}:{port}/docs")
    server.serve_forever()


if __name__ == "__main__":
    run()
