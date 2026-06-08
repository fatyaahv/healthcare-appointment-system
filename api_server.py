from __future__ import annotations

import hashlib
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
PORTAL_DATA_FILE = BASE_DIR / "portal_data.xml"
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
MASTER_USERNAME = "master"
MASTER_PASSWORD = "123456"

# Portal doctors and selectable location/department data are intentionally code-defined.
# Patients cannot register doctor accounts.
LOCATION_CATALOG = {
    "cities": [
        {
            "cityId": "IST",
            "cityName": "Istanbul",
            "districts": [
                {
                    "districtId": "UMR",
                    "districtName": "Umraniye",
                    "hospitals": [
                        {
                            "hospitalId": "H01",
                            "hospitalName": "Umraniye Egitim ve Arastirma Hastanesi",
                        }
                    ],
                }
            ],
        }
    ],
    "departments": [
        {"departmentId": "CARD", "departmentName": "Kardiyoloji"},
        {"departmentId": "EYE", "departmentName": "Goz Hastaliklari"},
        {"departmentId": "PED", "departmentName": "Cocuk Sagligi"},
        {"departmentId": "ORT", "departmentName": "Ortopedi"},
        {"departmentId": "DERM", "departmentName": "Dermatoloji"},
    ],
}

PORTAL_DOCTORS = [
    {"doctorId": "D01", "firstName": "Ahmet", "lastName": "Yilmaz", "departmentId": "CARD", "loginCode": "1001"},
    {"doctorId": "D02", "firstName": "Elif", "lastName": "Kaya", "departmentId": "CARD", "loginCode": "1002"},
    {"doctorId": "D03", "firstName": "Mert", "lastName": "Aydin", "departmentId": "CARD", "loginCode": "1003"},
    {"doctorId": "D04", "firstName": "Can", "lastName": "Demir", "departmentId": "EYE", "loginCode": "1004"},
    {"doctorId": "D05", "firstName": "Zeynep", "lastName": "Sahin", "departmentId": "EYE", "loginCode": "1005"},
    {"doctorId": "D06", "firstName": "Deniz", "lastName": "Arslan", "departmentId": "EYE", "loginCode": "1006"},
    {"doctorId": "D07", "firstName": "Murat", "lastName": "Celik", "departmentId": "PED", "loginCode": "1007"},
    {"doctorId": "D08", "firstName": "Selin", "lastName": "Yildiz", "departmentId": "PED", "loginCode": "1008"},
    {"doctorId": "D09", "firstName": "Burak", "lastName": "Ozturk", "departmentId": "PED", "loginCode": "1009"},
    {"doctorId": "D10", "firstName": "Hakan", "lastName": "Arslan", "departmentId": "ORT", "loginCode": "1010"},
    {"doctorId": "D11", "firstName": "Yasemin", "lastName": "Bulut", "departmentId": "ORT", "loginCode": "1011"},
    {"doctorId": "D12", "firstName": "Omer", "lastName": "Faruk", "departmentId": "ORT", "loginCode": "1012"},
    {"doctorId": "D13", "firstName": "Merve", "lastName": "Acar", "departmentId": "DERM", "loginCode": "1013"},
    {"doctorId": "D14", "firstName": "Kerem", "lastName": "Polat", "departmentId": "DERM", "loginCode": "1014"},
    {"doctorId": "D15", "firstName": "Ece", "lastName": "Kurt", "departmentId": "DERM", "loginCode": "1015"},
]


def catalog_hospital() -> dict[str, str]:
    return LOCATION_CATALOG["cities"][0]["districts"][0]["hospitals"][0]


def department_name(department_id: str) -> str:
    department = next(
        (item for item in LOCATION_CATALOG["departments"] if item["departmentId"] == department_id),
        None,
    )
    return department["departmentName"] if department else ""


def decorate_portal_doctor(doctor: dict[str, str]) -> dict[str, str]:
    hospital = catalog_hospital()
    return {
        **doctor,
        "cityId": doctor.get("cityId", "IST"),
        "cityName": doctor.get("cityName", "Istanbul"),
        "districtId": doctor.get("districtId", "UMR"),
        "districtName": doctor.get("districtName", "Umraniye"),
        "hospitalId": doctor.get("hospitalId", hospital["hospitalId"]),
        "hospitalName": doctor.get("hospitalName", hospital["hospitalName"]),
        "departmentName": department_name(doctor["departmentId"]),
    }


def portal_doctor(doctor_id: str, doctors: list[dict[str, str]] | None = None) -> dict[str, str] | None:
    source = doctors if doctors is not None else PORTAL_DOCTORS
    doctor = next((item for item in source if item["doctorId"].upper() == doctor_id.upper()), None)
    if not doctor:
        return None
    return decorate_portal_doctor(doctor)


def list_portal_doctors(doctors: list[dict[str, str]] | None = None) -> list[dict[str, str]]:
    source = doctors if doctors is not None else PORTAL_DOCTORS
    return [decorate_portal_doctor(doctor) for doctor in source]


def text(parent: ET.Element, query: str) -> str:
    node = parent.find(query, NS)
    return node.text.strip() if node is not None and node.text else ""


def first_query_value(query: dict[str, list[str]], name: str) -> str | None:
    values = query.get(name)
    return values[0] if values else None


def parse_request_body(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length", "0"))
    if length == 0:
        return {}
    raw_body = handler.rfile.read(length).decode("utf-8")
    content_type = handler.headers.get("Content-Type", "")
    if "application/xml" in content_type or "text/xml" in content_type:
        try:
            root = ET.fromstring(raw_body)
        except ET.ParseError as exc:
            raise ValueError(f"Invalid XML request body: {exc}") from exc
        return {child.tag: child.text.strip() if child.text else "" for child in root}
    return {key: values[0] for key, values in parse_qs(raw_body).items()}


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


def add_text(parent: ET.Element, tag: str, value: Any) -> ET.Element:
    node = ET.SubElement(parent, tag)
    if value is None:
        node.text = ""
    elif isinstance(value, bool):
        node.text = "true" if value else "false"
    else:
        node.text = str(value)
    return node


def append_xml(parent: ET.Element, key: str, value: Any) -> None:
    if isinstance(value, dict):
        node = ET.SubElement(parent, key)
        for child_key, child_value in value.items():
            append_xml(node, child_key, child_value)
    elif isinstance(value, list):
        list_node = ET.SubElement(parent, key)
        item_tag = key[:-1] if key.endswith("s") else "item"
        for item in value:
            append_xml(list_node, item_tag, item)
    else:
        add_text(parent, key, value)


def payload_to_xml(payload: dict[str, Any], root_name: str = "response") -> bytes:
    root = ET.Element(root_name)
    for key, value in payload.items():
        append_xml(root, key, value)
    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def node_text(parent: ET.Element, tag: str) -> str:
    node = parent.find(tag)
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
            self._save({"patients": [], "slots": [], "doctors": []})

    def _load(self) -> dict[str, Any]:
        root = ET.parse(self.data_path).getroot()
        patients = []
        for patient in root.findall("patients/patient"):
            patients.append(
                {
                    "tc": node_text(patient, "tc"),
                    "birthDate": node_text(patient, "birthDate"),
                    "firstName": node_text(patient, "firstName"),
                    "lastName": node_text(patient, "lastName"),
                }
            )
        doctors = []
        for doctor in root.findall("doctors/doctor"):
            doctors.append(
                {
                    "doctorId": node_text(doctor, "doctorId"),
                    "firstName": node_text(doctor, "firstName"),
                    "lastName": node_text(doctor, "lastName"),
                    "departmentId": node_text(doctor, "departmentId"),
                    "hospitalId": node_text(doctor, "hospitalId") or "H01",
                    "loginCode": node_text(doctor, "loginCode"),
                }
            )
        slots = []
        for slot in root.findall("slots/slot"):
            slots.append(
                {
                    "slotId": node_text(slot, "slotId"),
                    "doctorId": node_text(slot, "doctorId"),
                    "cityId": node_text(slot, "cityId"),
                    "districtId": node_text(slot, "districtId"),
                    "hospitalId": node_text(slot, "hospitalId"),
                    "departmentId": node_text(slot, "departmentId"),
                    "date": node_text(slot, "date"),
                    "time": node_text(slot, "time"),
                    "durationMinutes": int(node_text(slot, "durationMinutes") or "15"),
                    "isBooked": node_text(slot, "isBooked") == "true",
                    "patientTc": node_text(slot, "patientTc") or None,
                }
            )
        return {"patients": patients, "slots": slots, "doctors": doctors}

    def _save(self, data: dict[str, Any]) -> None:
        root = ET.Element("portalData")
        patients_node = ET.SubElement(root, "patients")
        for patient in data["patients"]:
            patient_node = ET.SubElement(patients_node, "patient")
            add_text(patient_node, "tc", patient.get("tc", ""))
            add_text(patient_node, "birthDate", patient.get("birthDate", ""))
            add_text(patient_node, "firstName", patient.get("firstName", ""))
            add_text(patient_node, "lastName", patient.get("lastName", ""))

        doctors_node = ET.SubElement(root, "doctors")
        for doctor in data.get("doctors", []):
            doctor_node = ET.SubElement(doctors_node, "doctor")
            for field in ("doctorId", "firstName", "lastName", "departmentId", "hospitalId", "loginCode"):
                add_text(doctor_node, field, doctor.get(field, ""))

        slots_node = ET.SubElement(root, "slots")
        for slot in data.get("slots", []):
            slot_node = ET.SubElement(slots_node, "slot")
            for field in (
                "slotId",
                "doctorId",
                "cityId",
                "districtId",
                "hospitalId",
                "departmentId",
                "date",
                "time",
                "durationMinutes",
                "isBooked",
                "patientTc",
            ):
                add_text(slot_node, field, slot.get(field))

        ET.indent(root, space="  ")
        tree = ET.ElementTree(root)
        tree.write(self.data_path, encoding="utf-8", xml_declaration=True)

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

    def authenticate_master(self, payload: dict[str, Any]) -> dict[str, str]:
        ensure_required(payload, ["username", "password"])
        if str(payload["username"]).strip() != MASTER_USERNAME or str(payload["password"]).strip() != MASTER_PASSWORD:
            raise PermissionError("Master login failed. Check username and password.")
        return {"username": MASTER_USERNAME, "role": "master"}

    def list_doctors(self) -> list[dict[str, str]]:
        with self._lock:
            data = self._load()
            return list_portal_doctors(self._all_doctor_records(data))

    def add_doctor(self, payload: dict[str, Any]) -> dict[str, str]:
        self.authenticate_master(payload)
        ensure_required(payload, ["firstName", "lastName", "departmentId", "hospitalId", "loginCode"])
        department_id = str(payload["departmentId"]).strip().upper()
        hospital_id = str(payload["hospitalId"]).strip().upper()
        if not department_name(department_id):
            raise ValueError("departmentId is not in the catalog.")
        if hospital_id != catalog_hospital()["hospitalId"]:
            raise ValueError("hospitalId is not in the catalog.")

        with self._lock:
            data = self._load()
            doctor_records = self._all_doctor_records(data)
            doctor_id = str(payload.get("doctorId", "")).strip().upper() or self._next_doctor_id(doctor_records)
            if any(doctor["doctorId"].upper() == doctor_id for doctor in doctor_records):
                raise ValueError("doctorId already exists.")
            doctor = {
                "doctorId": doctor_id,
                "firstName": str(payload["firstName"]).strip(),
                "lastName": str(payload["lastName"]).strip(),
                "departmentId": department_id,
                "hospitalId": hospital_id,
                "loginCode": str(payload["loginCode"]).strip(),
            }
            data["doctors"].append(doctor)
            data["doctors"].sort(key=lambda item: item["doctorId"])
            self._save(data)
            return decorate_portal_doctor(doctor)

    def authenticate_doctor(self, doctor_id: str, code: str, repository: AppointmentRepository) -> dict[str, str]:
        doctor_id = doctor_id.upper().strip()
        with self._lock:
            data = self._load()
            doctor = portal_doctor(doctor_id, self._all_doctor_records(data))
        if doctor is None or doctor.get("loginCode") != str(code).strip():
            raise PermissionError("Doctor login failed. Check doctor ID and code.")
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
                        "cityId": doctor["cityId"],
                        "districtId": doctor["districtId"],
                        "hospitalId": doctor["hospitalId"],
                        "departmentId": doctor["departmentId"],
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

    def list_slots(
        self,
        repository: AppointmentRepository,
        doctor_id: str | None = None,
        slot_date: str | None = None,
        city_id: str | None = None,
        district_id: str | None = None,
        hospital_id: str | None = None,
        department_id: str | None = None,
    ) -> list[dict[str, Any]]:
        with self._lock:
            data = self._load()
            slots = [self._decorate_slot(slot, data, repository) for slot in data["slots"]]
        if city_id:
            slots = [slot for slot in slots if slot.get("cityId", "").upper() == city_id.upper()]
        if district_id:
            slots = [slot for slot in slots if slot.get("districtId", "").upper() == district_id.upper()]
        if hospital_id:
            slots = [slot for slot in slots if slot.get("hospitalId", "").upper() == hospital_id.upper()]
        if department_id:
            slots = [slot for slot in slots if slot.get("departmentId", "").upper() == department_id.upper()]
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

    def cancel_doctor_booking(self, slot_id: str, payload: dict[str, Any], repository: AppointmentRepository) -> dict[str, Any]:
        ensure_required(payload, ["doctorId", "code"])
        doctor = self.authenticate_doctor(str(payload["doctorId"]), str(payload["code"]), repository)
        with self._lock:
            data = self._load()
            slot = self._find_slot(data, slot_id)
            if not slot:
                raise LookupError("Slot was not found.")
            if slot["doctorId"] != doctor["doctorId"]:
                raise PermissionError("This doctor cannot cancel another doctor's appointment.")
            if not slot["isBooked"]:
                raise ValueError("This appointment slot is already empty.")
            slot["isBooked"] = False
            slot["patientTc"] = None
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

    def list_public_bookings(self, repository: AppointmentRepository) -> list[dict[str, Any]]:
        with self._lock:
            data = self._load()
            bookings = [
                self._decorate_slot(slot, data, repository)
                for slot in data["slots"]
                if slot["isBooked"]
            ]
        for booking in bookings:
            booking["patientPublic"] = self._public_patient(booking.get("patient"))
            booking.pop("patient", None)
            booking.pop("patientTc", None)
        return bookings

    def booked_count(self) -> int:
        with self._lock:
            return sum(1 for slot in self._load()["slots"] if slot["isBooked"])

    def patient_count(self) -> int:
        with self._lock:
            return len(self._load()["patients"])

    def doctor_count(self) -> int:
        with self._lock:
            return len(self._all_doctor_records(self._load()))

    def _find_patient(self, data: dict[str, Any], tc: str) -> dict[str, str] | None:
        return next((patient for patient in data["patients"] if patient["tc"] == tc), None)

    def _find_slot(self, data: dict[str, Any], slot_id: str) -> dict[str, Any] | None:
        return next((slot for slot in data["slots"] if slot["slotId"] == slot_id), None)

    def _all_doctor_records(self, data: dict[str, Any]) -> list[dict[str, str]]:
        return [*PORTAL_DOCTORS, *data.get("doctors", [])]

    def _next_doctor_id(self, doctors: list[dict[str, str]]) -> str:
        numbers = []
        for doctor in doctors:
            doctor_id = doctor.get("doctorId", "")
            if doctor_id.startswith("D") and doctor_id[1:].isdigit():
                numbers.append(int(doctor_id[1:]))
        return f"D{max(numbers, default=0) + 1:02d}"

    def _public_patient(self, patient: dict[str, str] | None) -> dict[str, str]:
        if not patient:
            return {"firstNamePrefix": "", "lastNamePrefix": "", "tcMaskedHash": ""}
        tc = patient.get("tc", "")
        digest = hashlib.sha256(tc.encode("utf-8")).hexdigest()[:8]
        return {
            "firstNamePrefix": patient.get("firstName", "")[:2],
            "lastNamePrefix": patient.get("lastName", "")[:2],
            "tcMaskedHash": f"{tc[:2]}******-{digest}",
        }

    def _decorate_slot(self, slot: dict[str, Any], data: dict[str, Any], repository: AppointmentRepository) -> dict[str, Any]:
        doctor = portal_doctor(slot["doctorId"], self._all_doctor_records(data)) or {
            "firstName": "",
            "lastName": "",
            "departmentName": "",
            "hospitalName": "",
            "cityName": "",
            "districtName": "",
        }
        patient = self._find_patient(data, slot["patientTc"]) if slot.get("patientTc") else None
        return {
            **slot,
            "doctorName": f"Dr. {doctor.get('firstName', '')} {doctor.get('lastName', '')}".strip(),
            "cityId": doctor.get("cityId", slot.get("cityId", "")),
            "cityName": doctor.get("cityName", ""),
            "districtId": doctor.get("districtId", slot.get("districtId", "")),
            "districtName": doctor.get("districtName", ""),
            "hospitalId": doctor.get("hospitalId", slot.get("hospitalId", "")),
            "hospitalName": doctor.get("hospitalName", ""),
            "departmentId": doctor.get("departmentId", slot.get("departmentId", "")),
            "departmentName": doctor.get("departmentName", ""),
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
        if method == "DELETE":
            return self.handle_delete(path, {}, query)
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
            summary = self.repository.appointment_summary()
            summary["totalAppointments"] = int(summary["totalAppointments"]) + self.portal_store.booked_count()
            summary["totalDoctors"] = self.portal_store.doctor_count()
            summary["totalPatients"] = self.portal_store.patient_count()
            return HTTPStatus.OK, summary
        if path == "/api/integration/holidays":
            year_value = first_query_value(query, "year") or str(datetime.now().year)
            country_code = first_query_value(query, "countryCode") or "TR"
            try:
                year = int(year_value)
            except ValueError:
                return HTTPStatus.BAD_REQUEST, {"error": "year must be a number."}
            return HTTPStatus.OK, self.holiday_service.get_public_holidays(year, country_code)
        if path == "/api/portal/catalog":
            return HTTPStatus.OK, LOCATION_CATALOG
        if path == "/api/portal/doctors":
            doctors = self.portal_store.list_doctors()
            department_id = first_query_value(query, "departmentId")
            hospital_id = first_query_value(query, "hospitalId")
            if department_id:
                doctors = [doctor for doctor in doctors if doctor["departmentId"].upper() == department_id.upper()]
            if hospital_id:
                doctors = [doctor for doctor in doctors if doctor["hospitalId"].upper() == hospital_id.upper()]
            return HTTPStatus.OK, {"doctors": doctors}
        if path == "/api/slots":
            return HTTPStatus.OK, {
                "slots": self.portal_store.list_slots(
                    self.repository,
                    doctor_id=first_query_value(query, "doctorId"),
                    slot_date=first_query_value(query, "date"),
                    city_id=first_query_value(query, "cityId"),
                    district_id=first_query_value(query, "districtId"),
                    hospital_id=first_query_value(query, "hospitalId"),
                    department_id=first_query_value(query, "departmentId"),
                )
            }
        if path == "/api/doctor/bookings":
            return HTTPStatus.OK, {"appointments": self.portal_store.list_doctor_bookings(query, self.repository)}
        if path == "/api/patient/bookings":
            return HTTPStatus.OK, {"appointments": self.portal_store.list_patient_bookings(query, self.repository)}
        if path == "/api/public/bookings":
            return HTTPStatus.OK, {"appointments": self.portal_store.list_public_bookings(self.repository)}
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
        if path == "/api/auth/master/login":
            master = self.portal_store.authenticate_master(payload)
            return HTTPStatus.OK, {"master": master}
        if path == "/api/master/doctors":
            doctor = self.portal_store.add_doctor(payload)
            return HTTPStatus.CREATED, {"doctor": doctor}
        if path == "/api/doctor/slots":
            slots = self.portal_store.create_slots(payload, self.repository)
            return HTTPStatus.CREATED, {"slots": slots}
        if path == "/api/patient/appointments":
            slot = self.portal_store.book_slot(payload, self.repository)
            return HTTPStatus.CREATED, {"appointment": slot}
        return HTTPStatus.NOT_FOUND, {"error": f"No route found for {path}"}

    def handle_delete(
        self,
        path: str,
        payload: dict[str, Any],
        query: dict[str, list[str]] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        if path.startswith("/api/doctor/bookings/"):
            slot_id = path.rsplit("/", 1)[-1]
            merged_payload = dict(payload)
            for key, values in (query or {}).items():
                if values:
                    merged_payload[key] = values[0]
            slot = self.portal_store.cancel_doctor_booking(slot_id, merged_payload, self.repository)
            return HTTPStatus.OK, {"appointment": slot}
        return HTTPStatus.NOT_FOUND, {"error": f"No route found for {path}"}


class RequestHandler(BaseHTTPRequestHandler):
    api = AppointmentApi(AppointmentRepository(), HolidayService(), PortalStore())

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
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
        if parsed.path == "/openapi.xml":
            self.send_xml(HTTPStatus.OK, build_openapi_document())
            return

        self._send_api_response(lambda: self.api.handle_get(parsed.path, parse_qs(parsed.query)))

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        self._send_api_response(lambda: self.api.handle_post(parsed.path, parse_request_body(self)))

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        self._send_api_response(lambda: self.api.handle_delete(parsed.path, parse_request_body(self), parse_qs(parsed.query)))

    def _send_api_response(self, handler) -> None:
        try:
            status, payload = handler()
        except ValueError as exc:
            status, payload = HTTPStatus.BAD_REQUEST, {"error": str(exc)}
        except PermissionError as exc:
            status, payload = HTTPStatus.UNAUTHORIZED, {"error": str(exc)}
        except LookupError as exc:
            status, payload = HTTPStatus.NOT_FOUND, {"error": str(exc)}
        except Exception as exc:
            status, payload = HTTPStatus.INTERNAL_SERVER_ERROR, {"error": f"Internal server error: {exc}"}
        self.send_xml(status, payload)

    def send_xml(self, status: int, payload: dict[str, Any]) -> None:
        body = payload_to_xml(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/xml; charset=utf-8")
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
            self.send_xml(HTTPStatus.FORBIDDEN, {"error": "Forbidden"})
            return
        if not resolved.exists() or not resolved.is_file():
            self.send_xml(HTTPStatus.NOT_FOUND, {"error": "File not found"})
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


def build_openapi_document() -> dict[str, Any]:
    return {
        "info": {
            "title": "Healthcare Appointment System API",
            "version": "1.2.0",
            "description": "XML-based healthcare appointment portal API.",
        },
        "servers": [{"url": "http://127.0.0.1:8000"}],
        "paths": {
            "path": [
                {"url": "/api/health", "method": "GET", "summary": "Check API health"},
                {"url": "/api/portal/catalog", "method": "GET", "summary": "List cities, districts, hospitals, and departments"},
                {"url": "/api/portal/doctors", "method": "GET", "summary": "List code-defined doctors"},
                {"url": "/api/slots", "method": "GET", "summary": "List doctor-created appointment slots"},
                {"url": "/api/auth/patient/register", "method": "POST", "summary": "Register patient"},
                {"url": "/api/auth/patient/login", "method": "POST", "summary": "Login patient"},
                {"url": "/api/auth/doctor/login", "method": "POST", "summary": "Login doctor"},
                {"url": "/api/auth/master/login", "method": "POST", "summary": "Login master user"},
                {"url": "/api/master/doctors", "method": "POST", "summary": "Create a doctor with XML-compatible data"},
                {"url": "/api/doctor/slots", "method": "POST", "summary": "Create 15-minute doctor slots"},
                {"url": "/api/patient/appointments", "method": "POST", "summary": "Book an available appointment slot"},
                {"url": "/api/doctor/bookings", "method": "GET", "summary": "List booked patients for a doctor"},
                {"url": "/api/doctor/bookings/{slotId}", "method": "DELETE", "summary": "Cancel a booked appointment"},
                {"url": "/api/patient/bookings", "method": "GET", "summary": "List patient bookings"},
            ]
        },
    }


def swagger_ui_html() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Healthcare Appointment System API Docs</title>
  <style>
    body { margin: 0; font-family: Arial, sans-serif; color: #102033; background: #f6f7f9; }
    main { width: min(980px, calc(100% - 32px)); margin: 40px auto; }
    h1 { margin-bottom: 8px; color: #142f4c; }
    .panel { background: #fff; border: 1px solid #d9e0e8; border-radius: 8px; padding: 20px; }
    table { width: 100%; border-collapse: collapse; margin-top: 18px; background: #fff; }
    th, td { padding: 12px 14px; border-bottom: 1px solid #d9e0e8; text-align: left; }
    th { background: #edf3f8; color: #142f4c; }
    code { font-family: Consolas, monospace; color: #8a1f2d; }
    .method { font-weight: 800; color: #0f654f; }
  </style>
</head>
<body>
  <main>
    <h1>Healthcare Appointment System API Docs</h1>
    <p>Backend documentation page. The frontend intentionally does not link here.</p>
    <div class="panel">
      <p>OpenAPI-style XML document:</p>
      <p><a href="/openapi.xml">/openapi.xml</a></p>
      <table>
        <thead>
          <tr><th>Method</th><th>Endpoint</th><th>Description</th></tr>
        </thead>
        <tbody>
          <tr><td class="method">GET</td><td><code>/api/health</code></td><td>Check API health</td></tr>
          <tr><td class="method">GET</td><td><code>/api/portal/catalog</code></td><td>List city, district, hospital, and department selections</td></tr>
          <tr><td class="method">GET</td><td><code>/api/portal/doctors</code></td><td>List code-defined doctors</td></tr>
          <tr><td class="method">GET</td><td><code>/api/slots</code></td><td>List appointment slots with filters</td></tr>
          <tr><td class="method">POST</td><td><code>/api/auth/patient/register</code></td><td>Register patient</td></tr>
          <tr><td class="method">POST</td><td><code>/api/auth/patient/login</code></td><td>Login patient</td></tr>
          <tr><td class="method">POST</td><td><code>/api/auth/doctor/login</code></td><td>Login doctor</td></tr>
          <tr><td class="method">POST</td><td><code>/api/auth/master/login</code></td><td>Login master user</td></tr>
          <tr><td class="method">POST</td><td><code>/api/master/doctors</code></td><td>Master creates a doctor</td></tr>
          <tr><td class="method">POST</td><td><code>/api/doctor/slots</code></td><td>Create 15-minute doctor slots</td></tr>
          <tr><td class="method">POST</td><td><code>/api/patient/appointments</code></td><td>Book slot</td></tr>
          <tr><td class="method">GET</td><td><code>/api/doctor/bookings</code></td><td>Doctor sees booked patient name, surname, and TC</td></tr>
          <tr><td class="method">DELETE</td><td><code>/api/doctor/bookings/{slotId}</code></td><td>Doctor cancels a booked appointment</td></tr>
        </tbody>
      </table>
    </div>
  </main>
</body>
</html>"""


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), RequestHandler)
    print(f"API running at http://{host}:{port}")
    print(f"Backend docs at http://{host}:{port}/docs")
    server.serve_forever()


if __name__ == "__main__":
    run()
