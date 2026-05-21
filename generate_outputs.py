from collections import Counter
from pathlib import Path
from xml.dom import minidom
from xml.etree import ElementTree as ET


XML_FILE = Path("appointments.xml")
OUTPUT_DIR = Path("outputs")
DOCTOR_ID = "D01"
NS_URI = "https://www.saglikrandevu.com/schema"
NS = {"h": NS_URI}


def text(parent: ET.Element, query: str) -> str:
    node = parent.find(query, NS)
    return node.text.strip() if node is not None and node.text else ""


def add_text(parent: ET.Element, tag: str, value: str) -> ET.Element:
    node = ET.SubElement(parent, tag)
    node.text = value
    return node


def write_pretty_xml(root: ET.Element, path: Path) -> None:
    xml_bytes = ET.tostring(root, encoding="utf-8")
    pretty = minidom.parseString(xml_bytes).toprettyxml(indent="    ", encoding="UTF-8")
    path.write_bytes(pretty)


def create_summary(appointments: list[ET.Element]) -> ET.Element:
    status_counts = Counter(text(item, "h:status") for item in appointments)
    root = ET.Element("appointmentSummary")
    add_text(root, "totalAppointments", str(len(appointments)))
    add_text(root, "pending", str(status_counts["Pending"]))
    add_text(root, "completed", str(status_counts["Completed"]))
    add_text(root, "cancelled", str(status_counts["Cancelled"]))
    return root


def create_filtered_appointments(appointments: list[ET.Element], status: str) -> ET.Element:
    root = ET.Element("filteredAppointments")
    root.set("status", status)

    for item in appointments:
        if text(item, "h:status") != status:
            continue

        appointment = ET.SubElement(root, "appointment")
        for field in ("appointmentId", "doctorId", "patientId", "appointmentDateTime", "status", "notes"):
            add_text(appointment, field, text(item, f"h:{field}"))

    return root


def create_doctor_schedule(appointments: list[ET.Element], doctor_id: str) -> ET.Element:
    root = ET.Element("doctorSchedule")
    root.set("doctorId", doctor_id)

    for item in appointments:
        if text(item, "h:doctorId") != doctor_id:
            continue

        appointment = ET.SubElement(root, "appointment")
        add_text(appointment, "appointmentId", text(item, "h:appointmentId"))
        add_text(appointment, "patientId", text(item, "h:patientId"))
        add_text(appointment, "appointmentDateTime", text(item, "h:appointmentDateTime"))
        add_text(appointment, "status", text(item, "h:status"))
        add_text(appointment, "notes", text(item, "h:notes"))

    return root


def main() -> None:
    try:
        tree = ET.parse(XML_FILE)
    except FileNotFoundError:
        print(f"File error: missing XML file: {XML_FILE}")
        return
    except ET.ParseError as exc:
        print(f"XML parse error: {exc}")
        return

    root = tree.getroot()
    appointments = root.findall("h:appointments/h:appointment", NS)
    if not appointments:
        print("No appointments found; output files were not created.")
        return

    OUTPUT_DIR.mkdir(exist_ok=True)
    write_pretty_xml(create_summary(appointments), OUTPUT_DIR / "appointment_summary.xml")
    write_pretty_xml(create_filtered_appointments(appointments, "Pending"), OUTPUT_DIR / "pending_appointments.xml")
    write_pretty_xml(create_doctor_schedule(appointments, DOCTOR_ID), OUTPUT_DIR / f"doctor_schedule_{DOCTOR_ID}.xml")

    print("Generated XML outputs:")
    print(f"  {OUTPUT_DIR / 'appointment_summary.xml'}")
    print(f"  {OUTPUT_DIR / 'pending_appointments.xml'}")
    print(f"  {OUTPUT_DIR / f'doctor_schedule_{DOCTOR_ID}.xml'}")


if __name__ == "__main__":
    main()
