from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET


XML_FILE = Path("appointments.xml")
XSD_FILE = Path("healthcare.xsd")
NS = {"h": "https://www.saglikrandevu.com/schema"}


def validate_with_xsd(xml_path: Path, xsd_path: Path) -> bool:
    """Validate XML if lxml is installed; otherwise continue with parsing."""
    try:
        from lxml import etree
    except ImportError:
        print("XSD validation skipped: install lxml to enable schema validation.")
        return True

    try:
        schema_doc = etree.parse(str(xsd_path))
        schema = etree.XMLSchema(schema_doc)
        xml_doc = etree.parse(str(xml_path))
        schema.assertValid(xml_doc)
        print("XSD validation: valid")
        return True
    except (etree.XMLSyntaxError, etree.DocumentInvalid, OSError) as exc:
        print(f"XSD validation failed: {exc}")
        return False


def text(parent: ET.Element, query: str) -> str:
    node = parent.find(query, NS)
    return node.text.strip() if node is not None and node.text else ""


def main() -> None:
    try:
        if not XML_FILE.exists():
            raise FileNotFoundError(f"Missing XML file: {XML_FILE}")

        if XSD_FILE.exists():
            validate_with_xsd(XML_FILE, XSD_FILE)

        tree = ET.parse(XML_FILE)
        root = tree.getroot()
    except FileNotFoundError as exc:
        print(f"File error: {exc}")
        return
    except ET.ParseError as exc:
        print(f"XML parse error: {exc}")
        return

    appointments = root.findall("h:appointments/h:appointment", NS)
    if not appointments:
        print("No appointments found.")
        return

    status_counts = Counter(text(item, "h:status") for item in appointments)
    doctor_counts = Counter(text(item, "h:doctorId") for item in appointments)

    print("DOM Parser Report")
    print(f"Total appointments: {len(appointments)}")
    print("Status counts:")
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")

    print("Appointments per doctor:")
    for doctor_id, count in sorted(doctor_counts.items()):
        print(f"  {doctor_id}: {count}")

    print("First five appointments:")
    for item in appointments[:5]:
        appointment_id = text(item, "h:appointmentId")
        patient_id = text(item, "h:patientId")
        doctor_id = text(item, "h:doctorId")
        appointment_time = text(item, "h:appointmentDateTime")
        status = text(item, "h:status")
        print(f"  {appointment_id}: {appointment_time}, patient={patient_id}, doctor={doctor_id}, status={status}")


if __name__ == "__main__":
    main()
