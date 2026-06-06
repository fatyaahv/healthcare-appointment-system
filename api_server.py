from __future__ import annotations

import json
import mimetypes
import re
import threading
from datetime import date, datetime, time, timedelta
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse
from xml.etree import ElementTree as ET

from external_service import HolidayService


BASE_DIR = Path(__file__).resolve().parent
XML_FILE = BASE_DIR / "appointments.xml"
PORTAL_DATA_FILE = BASE_DIR / "portal_data.json"
STATIC_FILES = {
    "/": BASE_DIR / "index.html",
    "/index.html": BASE_DIR / "index.html",
    "/styles.css": BASE_DIR / "styles.css",
    "/app.js": BASE_DIR / "app.js",
}
NS_URI = "https://www.saglikrandevu.com/schema"
NS = {"h": NS_URI}
ALLOWED_STATUSES = {"Pending", "Completed", "Cancelled"}
TC_PATTERN = re.compile(r"^\d{11}$")

# Doctors are intentionally code-defined. Patients cannot register doctor accounts.
DOCTOR_CODES = {
    "D01": "1001",
    "D02": "1002",
    "D03": "1003",
    "D04": "1004",
    "D05": "1005",
}


def text(parent: ET.Element, query: str) -> str:
    node = parent.find(query, NS)
    return node.text.strip() if node is not None and node.text else ""


def first_query_value(query: dict[str, list[str]], name: str) -> str | None:
    values = query.get(name)
    return values[0] if values else None


def parse_json_body(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length", "0"))
    if length == 0:
        return {}
    raw_body = handler.rfile.read(length).decode("utf-8")
    return json.loads(raw_body)


def parse_date(value: str, field_name: str = "date") -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(f"{field_name} must use YYYY-MM-DD format.") from exc


def parse_time(value: str, field_name: str = "time") -> time:
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError as exc:
        raise ValueError(f"{field_name} must use HH:MM format.") from exc


def ensure_tc(value: str) -> str:
    tc = str(value or "").strip()
    if not TC_PATTERN.fullmatch(tc):
        raise ValueError("TC must be exactly 11 digits.")
    return tc


def ensure_required(payload: dict[str, Any], names: list[str]) -> None:
    missing = [name for name in names if not str(payload.get(name, "")).strip()]
    if missing:
        raise ValueError(f"Missing required field(s): {', '.join(missing)}")


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

    def get_doctor(self, doctor_id: str) -> dict[str, str] | None:
        for doctor in self.list_doctors():
            if doctor["doctorId"].upper() == doctor_id.upper():
                return doctor
        return None

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


class PortalStore:
    def __init__(self, data_path: Path = PORTAL_DATA_FILE) -> None:
        self.data_path = data_path
        self._lock = threading.Lock()
        if not self.data_path.exists():
            self._save({"patients": [], "slots": []})

    def _load(self) -> dict[str, Any]:
        return json.loads(self.data_path.read_text(encoding="utf-8"))

    def _save(self, data: dict[str, Any]) -> None:
        self.data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def register_patient(self, payload: dict[str, Any]) -> dict[str, str]:
        ensure_required(payload, ["tc", "birthDate", "firstName", "lastName"])
        tc = ensure_tc(payload["tc"])
        birth_date = parse_date(str(payload["birthDate"]), "birthDate").isoformat()
        patient = {
            "tc": tc,
            "birthDate": birth_date,
            "firstName": str(payload["firstName"]).strip(),
            "lastName": str(payload["lastName"]).strip(),
        }

        with self._lock:
            data = self._load()
            existing = self._find_patient(data, tc)
            if existing and existing["birthDate"] != birth_date:
                raise ValueError("This TC is already registered with a different birth date.")
            if existing:
                existing.update(patient)
                patient = existing
            else:
                data["patients"].append(patient)
            self._save(data)
        return patient

    def login_patient(self, payload: dict[str, Any]) -> dict[str, str]:
        ensure_required(payload, ["tc", "birthDate"])
        tc = ensure_tc(payload["tc"])
        birth_date = parse_date(str(payload["birthDate"]), "birthDate").isoformat()

        with self._lock:
            data = self._load()
            patient = self._find_patient(data, tc)
        if not patient or patient["birthDate"] != birth_date:
            raise PermissionError("Patient login failed. Check TC and birth date.")
        return patient

    def authenticate_doctor(self, doctor_id: str, code: str, repository: AppointmentRepository) -> dict[str, str]:
        doctor_id = doctor_id.upper().strip()
        if DOCTOR_CODES.get(doctor_id) != str(code).strip():
            raise PermissionError("Doctor login failed. Check doctor ID and code.")
        doctor = repository.get_doctor(doctor_id)
        if doctor is None:
            raise PermissionError("Doctor is not defined in the XML doctor registry.")
        return doctor

    def create_slots(self, payload: dict[str, Any], repository: AppointmentRepository) -> list[dict[str, Any]]:
        ensure_required(payload, ["doctorId", "code", "date", "startTime", "endTime"])
        doctor = self.authenticate_doctor(str(payload["doctorId"]), str(payload["code"]), repository)
        slot_date = parse_date(str(payload["date"])).isoformat()
        start_time = parse_time(str(payload["startTime"]), "startTime")
        end_time = parse_time(str(payload["endTime"]), "endTime")
        start_dt = datetime.combine(date.fromisoformat(slot_date), start_time)
        end_dt = datetime.combine(date.fromisoformat(slot_date), end_time)
        if end_dt <= start_dt:
            raise ValueError("endTime must be later than startTime.")

        created: list[dict[str, Any]] = []
        with self._lock:
            data = self._load()
            existing_ids = {slot["slotId"] for slot in data["slots"]}
            cursor = start_dt
            while cursor + timedelta(minutes=15) <= end_dt:
                slot_id = f"{doctor['doctorId']}-{cursor.strftime('%Y%m%d%H%M')}"
                if slot_id not in existing_ids:
                    slot = {
                        "slotId": slot_id,
                        "doctorId": doctor["doctorId"],
                        "date": slot_date,
                        "time": cursor.strftime("%H:%M"),
                        "durationMinutes": 15,
                        "isBooked": False,
                        "patientTc": None,
                    }
                    data["slots"].append(slot)
                    created.append(slot)
                    existing_ids.add(slot_id)
                cursor += timedelta(minutes=15)
            data["slots"].sort(key=lambda item: (item["date"], item["time"], item["doctorId"]))
            self._save(data)
        return created

    def list_slots(self, repository: AppointmentRepository, doctor_id: str | None = None, slot_date: str | None = None) -> list[dict[str, Any]]:
        with self._lock:
            data = self._load()
            slots = [self._decorate_slot(slot, data, repository) for slot in data["slots"]]
        if doctor_id:
            slots = [slot for slot in slots if slot["doctorId"].upper() == doctor_id.upper()]
        if slot_date:
            slots = [slot for slot in slots if slot["date"] == slot_date]
        return slots

    def book_slot(self, payload: dict[str, Any], repository: AppointmentRepository) -> dict[str, Any]:
        ensure_required(payload, ["tc", "birthDate", "slotId"])
        patient = self.login_patient(payload)
        slot_id = str(payload["slotId"]).strip()

        with self._lock:
            data = self._load()
            slot = self._find_slot(data, slot_id)
            if not slot:
                raise LookupError("Slot was not found.")
            if slot["isBooked"]:
                raise ValueError("This appointment slot is already booked.")
            slot["isBooked"] = True
            slot["patientTc"] = patient["tc"]
            self._save(data)
            return self._decorate_slot(slot, data, repository)

    def list_doctor_bookings(self, query: dict[str, list[str]], repository: AppointmentRepository) -> list[dict[str, Any]]:
        doctor_id = first_query_value(query, "doctorId") or ""
        code = first_query_value(query, "code") or ""
        doctor = self.authenticate_doctor(doctor_id, code, repository)
        with self._lock:
            data = self._load()
            return [
                self._decorate_slot(slot, data, repository)
                for slot in data["slots"]
                if slot["doctorId"] == doctor["doctorId"] and slot["isBooked"]
            ]

    def list_patient_bookings(self, query: dict[str, list[str]], repository: AppointmentRepository) -> list[dict[str, Any]]:
        patient = self.login_patient(
            {
                "tc": first_query_value(query, "tc") or "",
                "birthDate": first_query_value(query, "birthDate") or "",
            }
        )
        with self._lock:
            data = self._load()
            return [
                self._decorate_slot(slot, data, repository)
                for slot in data["slots"]
                if slot["patientTc"] == patient["tc"]
            ]

    def _find_patient(self, data: dict[str, Any], tc: str) -> dict[str, str] | None:
        return next((patient for patient in data["patients"] if patient["tc"] == tc), None)

    def _find_slot(self, data: dict[str, Any], slot_id: str) -> dict[str, Any] | None:
        return next((slot for slot in data["slots"] if slot["slotId"] == slot_id), None)

    def _decorate_slot(self, slot: dict[str, Any], data: dict[str, Any], repository: AppointmentRepository) -> dict[str, Any]:
        doctor = repository.get_doctor(slot["doctorId"]) or {"firstName": "", "lastName": "", "clinicName": ""}
        patient = self._find_patient(data, slot["patientTc"]) if slot.get("patientTc") else None
        return {
            **slot,
            "doctorName": f"Dr. {doctor.get('firstName', '')} {doctor.get('lastName', '')}".strip(),
            "clinicName": doctor.get("clinicName", ""),
            "patient": patient,
        }


class AppointmentApi:
    def __init__(
        self,
        repository: AppointmentRepository,
        holiday_service: HolidayService,
        portal_store: PortalStore | None = None,
    ) -> None:
        self.repository = repository
        self.holiday_service = holiday_service
        self.portal_store = portal_store or PortalStore()

    def handle(self, method: str, path: str, query: dict[str, list[str]]) -> tuple[int, dict[str, Any]]:
        if method == "GET":
            return self.handle_get(path, query)
        return HTTPStatus.METHOD_NOT_ALLOWED, {"error": "Only GET endpoints are supported by this compatibility method."}

    def handle_get(self, path: str, query: dict[str, list[str]]) -> tuple[int, dict[str, Any]]:
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
        if path == "/api/portal/doctors":
            doctors = [
                {**doctor, "loginCode": DOCTOR_CODES.get(doctor["doctorId"], "")}
                for doctor in self.repository.list_doctors()
                if doctor["doctorId"] in DOCTOR_CODES
            ]
            return HTTPStatus.OK, {"doctors": doctors}
        if path == "/api/slots":
            return HTTPStatus.OK, {
                "slots": self.portal_store.list_slots(
                    self.repository,
                    doctor_id=first_query_value(query, "doctorId"),
                    slot_date=first_query_value(query, "date"),
                )
            }
        if path == "/api/doctor/bookings":
            return HTTPStatus.OK, {"appointments": self.portal_store.list_doctor_bookings(query, self.repository)}
        if path == "/api/patient/bookings":
            return HTTPStatus.OK, {"appointments": self.portal_store.list_patient_bookings(query, self.repository)}
        return HTTPStatus.NOT_FOUND, {"error": f"No route found for {path}"}

    def handle_post(self, path: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        if path == "/api/auth/patient/register":
            patient = self.portal_store.register_patient(payload)
            return HTTPStatus.CREATED, {"patient": patient}
        if path == "/api/auth/patient/login":
            patient = self.portal_store.login_patient(payload)
            return HTTPStatus.OK, {"patient": patient}
        if path == "/api/auth/doctor/login":
            ensure_required(payload, ["doctorId", "code"])
            doctor = self.portal_store.authenticate_doctor(str(payload["doctorId"]), str(payload["code"]), self.repository)
            return HTTPStatus.OK, {"doctor": doctor}
        if path == "/api/doctor/slots":
            slots = self.portal_store.create_slots(payload, self.repository)
            return HTTPStatus.CREATED, {"slots": slots}
        if path == "/api/patient/appointments":
            slot = self.portal_store.book_slot(payload, self.repository)
            return HTTPStatus.CREATED, {"appointment": slot}
        return HTTPStatus.NOT_FOUND, {"error": f"No route found for {path}"}


def build_openapi_document() -> dict[str, Any]:
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "Healthcare Appointment System API",
            "version": "1.1.0",
            "description": "REST API for XML appointment data, patient registration, doctor slot management, and appointment booking.",
        },
        "servers": [{"url": "http://localhost:8000"}],
        "paths": {
            "/api/health": {"get": {"summary": "Check API health", "responses": {"200": {"description": "API is running"}}}},
            "/api/clinics": {"get": {"summary": "List clinics and doctors", "responses": {"200": {"description": "Clinics returned"}}}},
            "/api/doctors": {"get": {"summary": "List doctors", "responses": {"200": {"description": "Doctors returned"}}}},
            "/api/appointments": {"get": {"summary": "List XML appointment records", "responses": {"200": {"description": "Appointments returned"}}}},
            "/api/portal/doctors": {"get": {"summary": "List code-defined doctors", "responses": {"200": {"description": "Doctors returned"}}}},
            "/api/slots": {"get": {"summary": "List doctor-created appointment slots", "responses": {"200": {"description": "Slots returned"}}}},
            "/api/auth/patient/register": {"post": {"summary": "Register patient with TC and birth date", "responses": {"201": {"description": "Patient registered"}}}},
            "/api/auth/patient/login": {"post": {"summary": "Login patient with TC and birth date", "responses": {"200": {"description": "Patient authenticated"}}}},
            "/api/auth/doctor/login": {"post": {"summary": "Login doctor with doctor ID and code", "responses": {"200": {"description": "Doctor authenticated"}}}},
            "/api/doctor/slots": {"post": {"summary": "Create 15-minute doctor slots", "responses": {"201": {"description": "Slots created"}}}},
            "/api/patient/appointments": {"post": {"summary": "Book an available appointment slot", "responses": {"201": {"description": "Appointment booked"}}}},
            "/api/doctor/bookings": {"get": {"summary": "List booked patients for a doctor", "responses": {"200": {"description": "Bookings returned"}}}},
            "/api/patient/bookings": {"get": {"summary": "List a patient's booked appointments", "responses": {"200": {"description": "Bookings returned"}}}},
            "/api/reports/summary": {"get": {"summary": "Get appointment totals", "responses": {"200": {"description": "Summary returned"}}}},
            "/api/integration/holidays": {"get": {"summary": "Fetch public holidays", "responses": {"200": {"description": "Holiday data returned"}}}},
        },
    }


class RequestHandler(BaseHTTPRequestHandler):
    api = AppointmentApi(AppointmentRepository(), HolidayService(), PortalStore())

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in STATIC_FILES:
            self.send_file(STATIC_FILES[parsed.path])
            return
        if parsed.path.startswith("/assets/"):
            self.send_file(BASE_DIR / parsed.path.lstrip("/"))
            return
        if parsed.path == "/docs":
            self.send_html(swagger_ui_html())
            return
        if parsed.path == "/openapi.json":
            self.send_json(HTTPStatus.OK, build_openapi_document())
            return

        self._send_api_response(lambda: self.api.handle_get(parsed.path, parse_qs(parsed.query)))

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        self._send_api_response(lambda: self.api.handle_post(parsed.path, parse_json_body(self)))

    def _send_api_response(self, handler) -> None:
        try:
            status, payload = handler()
        except json.JSONDecodeError:
            status, payload = HTTPStatus.BAD_REQUEST, {"error": "Request body must be valid JSON."}
        except ValueError as exc:
            status, payload = HTTPStatus.BAD_REQUEST, {"error": str(exc)}
        except PermissionError as exc:
            status, payload = HTTPStatus.UNAUTHORIZED, {"error": str(exc)}
        except LookupError as exc:
            status, payload = HTTPStatus.NOT_FOUND, {"error": str(exc)}
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

    def send_file(self, file_path: Path) -> None:
        resolved = file_path.resolve()
        if BASE_DIR not in resolved.parents and resolved != BASE_DIR:
            self.send_json(HTTPStatus.FORBIDDEN, {"error": "Forbidden"})
            return
        if not resolved.exists() or not resolved.is_file():
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "File not found"})
            return

        body = resolved.read_bytes()
        content_type = mimetypes.guess_type(resolved.name)[0] or "application/octet-stream"
        if resolved.suffix == ".js":
            content_type = "text/javascript"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
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
